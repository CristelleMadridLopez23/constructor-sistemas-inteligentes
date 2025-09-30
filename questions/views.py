from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
import json
from . import data_manager # Importamos el gestor de datos
# Create your views here.
class ConstructorView(View):

    # my_app/views.py

    def get(self, request, *args, **kwargs):
        """Muestra el formulario y la lista de preguntas."""
        questions = data_manager.get_questions()
        context = {
            
            'questions': questions, 
            'importance_levels': ['Low', 'Medium', 'High']
        }
        return render(request, 'constructor.html', context)

    def post(self, request, *args, **kwargs):
        """Recibe el POST del formulario, guarda la pregunta y retorna JSON."""
        # Se asume que los datos vienen como JSON para facilitar el manejo de las listas
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        # Aquí harías una validación más robusta
        if not data.get('question'):
            return JsonResponse({'status': 'error', 'message': 'Question text is required'}, status=400)

        new_question = data_manager.add_question(data)
        
        # Retorna la pregunta recién creada para actualizar el frontend
        return JsonResponse({
            'status': 'success',
            'question': new_question
        }, status=201)
