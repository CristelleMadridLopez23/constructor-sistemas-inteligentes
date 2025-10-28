from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import json
from . import data_manager # Importamos el gestor de datos
import io
import base64

# Matplotlib en modo headless para generar imágenes del árbol de decisión
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    plt = None

class AnswerQuestionsView(View):
    """Vista para el sistema experto de preguntas."""
    
    def get(self, request, *args, **kwargs):
        questions = data_manager.get_questions()
        first_questions = data_manager.get_next_questions(None, None)
        
        context = {
            'questions': json.dumps(questions),      # ← CON json.dumps()
            'first_questions': json.dumps(first_questions)  # ← CON json.dumps()
        }
        return render(request, 'answer.html', context)
    
    def post(self, request, *args, **kwargs):
        """Procesa las respuestas y retorna la siguiente pregunta."""
        try:
            data = json.loads(request.body)
            current_id = data.get('current_question')
            answer = data.get('answer')
            asked = set(data.get('asked_questions', []))
            
            # Obtener siguientes preguntas basadas en la respuesta
            next_questions = data_manager.get_next_questions(current_id, answer, asked)
            
            # Si no hay más preguntas, construir árbol de decisión
            # Si no hay más preguntas, construir árbol de decisión
            if not next_questions:
                answers_map = data.get('answers', {})
                tree = data_manager.build_decision_tree(answers_map)
                # Obtener inferencias (top 3 por ejemplo)
                inference = data_manager.infer_from_answers(answers_map, top_n=3)

                result = {
                        'status': 'completed',
                        'decision_tree': tree,
                        'inference': inference
                    }
                print(inference)

                # Intentar generar una imagen del árbol usando matplotlib
                if plt is not None:
                    try:
                        buf = io.BytesIO()
                        # Simple visualización: nodos en columna con flechas
                        fig, ax = plt.subplots(figsize=(6, max(2, len(tree) * 0.8)))
                        ax.axis('off')

                        y_start = len(tree) - 1
                        for i, node in enumerate(tree):
                            y = y_start - i
                            text = f"{node.get('id','')}: {node.get('question','')}\n→ {node.get('answer','')}"
                            ax.text(0.05, y, text, fontsize=10, va='center', bbox=dict(boxstyle='round', facecolor='#f7f7f7', edgecolor='#333'))
                            if i < len(tree) - 1:
                                # flecha hacia el siguiente
                                ax.annotate('', xy=(0.25, y - 0.15), xytext=(0.25, y - 0.6), arrowprops=dict(arrowstyle='->'))

                        plt.tight_layout()
                        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                        plt.close(fig)
                        buf.seek(0)
                        img_b64 = base64.b64encode(buf.read()).decode('ascii')
                        result['decision_tree_image'] = f"data:image/png;base64,{img_b64}"
                    except Exception as e:
                        # No detener el flujo si la generación de la imagen falla
                        print('Error generando imagen del árbol:', e)

                return JsonResponse(result)
            
            return JsonResponse({
                'status': 'next',
                'next_questions': next_questions
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

# Create your views here.
class ConstructorView(View):
    def get(self, request, *args, **kwargs):
        """Muestra el formulario y la lista de preguntas."""
        questions = data_manager.get_questions()
        context = {
            'questions': json.dumps(questions),  # ✨ Pasar como JSON string
            'questions_list': list(questions.values()),  # ✨ También como lista para el template
            'importance_levels': ['Low', 'Medium', 'High']
        }
        return render(request, 'constructor.html', context)


def upload_questions(request):
    """Recibe un archivo JSON con preguntas y las añade usando data_manager.

    Espera un archivo en request.FILES['file'] con contenido JSON. Retorna JsonResponse.
    """
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)

    try:
        raw = uploaded_file.read()
        text = raw.decode('utf-8')
        parsed = json.loads(text)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid JSON file: {e}'}, status=400)

    # Normalizar a una lista de preguntas
    questions_to_add = []
    if isinstance(parsed, dict):
        if 'questions' in parsed:
            q = parsed['questions']
            if isinstance(q, dict):
                questions_to_add = list(q.values())
            elif isinstance(q, list):
                questions_to_add = q
        else:
            if all(isinstance(v, dict) for v in parsed.values()):
                questions_to_add = list(parsed.values())
            else:
                return JsonResponse({'status': 'error', 'message': 'JSON structure not recognized'}, status=400)
    elif isinstance(parsed, list):
        questions_to_add = parsed
    else:
        return JsonResponse({'status': 'error', 'message': 'JSON must be an object or list'}, status=400)

    added = []
    for q in questions_to_add:
        if not isinstance(q, dict) or not q.get('question'):
            continue
        new_q = data_manager.add_question(q)
        added.append(new_q)

    return JsonResponse({
        'status': 'success', 
        'added_count': len(added), 
        'added': added
    })

    def post(self, request, *args, **kwargs):
        """Recibe el POST del formulario, guarda la pregunta y retorna JSON."""
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        if not data.get('question'):
            return JsonResponse({'status': 'error', 'message': 'Question text is required'}, status=400)

        new_question = data_manager.add_question(data)
        
        return JsonResponse({
            'status': 'success',
            'question': new_question
        }, status=201)

class EditorView(View):
    """Vista para editar preguntas existentes."""
    
    def get(self, request, *args, **kwargs):
        """Muestra la interfaz de edición con todas las preguntas."""
        questions = data_manager.get_questions()
        total_questions = data_manager.get_total_questions()
        next_id = data_manager.get_next_id_number()
        
        context = {
            'questions': json.dumps(questions),
            'questions_list': list(questions.values()),
            'total_questions': total_questions,
            'next_question_number': next_id,
            'importance_levels': ['Low', 'Medium', 'High']
        }
        return render(request, 'editor.html', context)
    
    def post(self, request, *args, **kwargs):
        """Actualiza una pregunta existente o importa preguntas desde un archivo JSON."""
        # Si se subió un archivo, manejar importación
        if request.FILES.get('file'):
            return upload_questions(request)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        
        question_id = data.get('id')
        if not question_id:
            return JsonResponse({'status': 'error', 'message': 'Question ID is required'}, status=400)
        
        # Actualizar la pregunta usando el data_manager
        updated_question = data_manager.update_question(question_id, data)
        
        if updated_question:
            return JsonResponse({
                'status': 'success',
                'question': updated_question
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Question not found'}, status=404)

    def delete(self, request, *args, **kwargs):
        """Elimina una pregunta existente."""
        try:
            data = json.loads(request.body.decode('utf-8'))
            question_id = data.get('id')
            
            if not question_id:
                return JsonResponse({'status': 'error', 'message': 'Question ID is required'}, status=400)
            
            success = data_manager.delete_question(question_id)
            
            if success:
                return JsonResponse({'status': 'success', 'message': 'Question deleted successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Question not found'}, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)