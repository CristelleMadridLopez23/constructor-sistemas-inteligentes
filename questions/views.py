from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import json
from . import data_manager # Importamos el gestor de datos
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
        """Actualiza una pregunta existente."""
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