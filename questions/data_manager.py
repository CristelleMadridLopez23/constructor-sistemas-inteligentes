import json
import os
from collections import defaultdict

# Define la ruta del archivo de almacenamiento (será la "persistencia" simulada)
DATA_FILE = 'questions.json'


QUESTIONS_STORE = {}
# Un diccionario simple para el grafo, donde la clave es el ID de la pregunta y el valor son sus dependencias.
QUESTION_GRAPH = defaultdict(list)
_NEXT_ID = 1

def _load_data():
    """Carga las preguntas desde el archivo JSON al inicio."""
    global QUESTIONS_STORE, _NEXT_ID, QUESTION_GRAPH
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            QUESTIONS_STORE = data.get('questions', {})
            _NEXT_ID = data.get('next_id', 1)
            # Reconstruir el grafo en memoria
            QUESTION_GRAPH = defaultdict(list)
            for q_id, q_data in QUESTIONS_STORE.items():
                for relation in q_data.get('relations', []):
                    QUESTION_GRAPH[q_id].append(relation)

    if not QUESTIONS_STORE:
        # Inicializar con el ID si no hay datos
        _NEXT_ID = 1

def _save_data():
    """Guarda las preguntas en el archivo JSON."""
    with open(DATA_FILE, 'w') as f:
        json.dump({
            'questions': QUESTIONS_STORE,
            'next_id': _NEXT_ID
        }, f, indent=4)

def get_questions():
    """Retorna todas las preguntas ordenadas por ID."""
    # Asegura que los datos se carguen al inicio de la ejecución.
    if not QUESTIONS_STORE and _NEXT_ID == 1:
        _load_data()
    return QUESTIONS_STORE

def add_question(data):
    """Añade una nueva pregunta y actualiza el grafo."""
    global _NEXT_ID
    new_id = f"Q-{_NEXT_ID:03d}"
    _NEXT_ID += 1
    
    question = {
        "id": new_id,
        "question": data.get('question', ''),
        "type": data.get('type', 'Simple'),
        "importance": data.get('importance', 'Low'),
        "answers": data.get('answers', []),
        "relations": data.get('relations', [])
    }
    
    QUESTIONS_STORE[new_id] = question
    
    # Actualiza el grafo (relaciones de salida)
    QUESTION_GRAPH[new_id] = question['relations']
    
    _save_data()
    return question

# Cargar los datos al importar el módulo
_load_data()