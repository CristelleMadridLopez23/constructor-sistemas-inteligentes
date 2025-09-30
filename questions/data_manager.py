import json
import os
from collections import defaultdict
from django.conf import settings

# Define la ruta del archivo de almacenamiento en el directorio del proyecto
DATA_FILE = os.path.join(settings.BASE_DIR, 'questions_data.json')

QUESTIONS_STORE = {}
QUESTION_GRAPH = defaultdict(list)
_NEXT_ID = 1
_DATA_LOADED = False

def _load_data():
    """Carga las preguntas desde el archivo JSON al inicio."""
    global QUESTIONS_STORE, _NEXT_ID, QUESTION_GRAPH, _DATA_LOADED
    
    if _DATA_LOADED:
        return
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                QUESTIONS_STORE = data.get('questions', {})
                _NEXT_ID = data.get('next_id', 1)
                
                # Reconstruir el grafo en memoria
                QUESTION_GRAPH = defaultdict(list)
                for q_id, q_data in QUESTIONS_STORE.items():
                    for relation in q_data.get('relations', []):
                        QUESTION_GRAPH[q_id].append(relation)
                
                print(f"✓ Datos cargados: {len(QUESTIONS_STORE)} preguntas, próximo ID: {_NEXT_ID}")
        else:
            print(f"✗ Archivo {DATA_FILE} no existe, iniciando con datos vacíos")
            QUESTIONS_STORE = {}
            _NEXT_ID = 1
            QUESTION_GRAPH = defaultdict(list)
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        QUESTIONS_STORE = {}
        _NEXT_ID = 1
        QUESTION_GRAPH = defaultdict(list)
    
    _DATA_LOADED = True

def _save_data():
    """Guarda las preguntas en el archivo JSON."""
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'questions': QUESTIONS_STORE,
                'next_id': _NEXT_ID
            }, f, indent=4, ensure_ascii=False)
        
        print(f"✓ Datos guardados en {DATA_FILE}")
    except Exception as e:
        print(f"Error al guardar datos: {e}")

def get_questions():
    """Retorna todas las preguntas ordenadas por ID."""
    _load_data()  # Siempre cargar antes de retornar
    return QUESTIONS_STORE

def add_question(data):
    """Añade una nueva pregunta y actualiza el grafo."""
    global _NEXT_ID
    
    _load_data()  # Cargar datos actuales
    
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
    
    _save_data()  # Guardar inmediatamente
    print(f"✓ Pregunta {new_id} añadida y guardada")
    return question

def update_question(question_id, data):
    """Actualiza una pregunta existente."""
    _load_data()
    
    if question_id not in QUESTIONS_STORE:
        return None
    
    # Actualizar los campos
    QUESTIONS_STORE[question_id].update({
        "question": data.get('question', QUESTIONS_STORE[question_id]['question']),
        "type": data.get('type', QUESTIONS_STORE[question_id]['type']),
        "importance": data.get('importance', QUESTIONS_STORE[question_id]['importance']),
        "answers": data.get('answers', QUESTIONS_STORE[question_id]['answers']),
        "relations": data.get('relations', QUESTIONS_STORE[question_id]['relations'])
    })
    
    # Actualizar el grafo
    QUESTION_GRAPH[question_id] = QUESTIONS_STORE[question_id]['relations']
    
    _save_data()
    print(f"✓ Pregunta {question_id} actualizada")
    return QUESTIONS_STORE[question_id]

def delete_question(question_id):
    """Elimina una pregunta y todas sus relaciones."""
    _load_data()
    
    if question_id not in QUESTIONS_STORE:
        return False
    
    # Eliminar la pregunta
    del QUESTIONS_STORE[question_id]
    
    # Eliminar del grafo
    if question_id in QUESTION_GRAPH:
        del QUESTION_GRAPH[question_id]
    
    # Eliminar todas las relaciones que apunten a esta pregunta
    for q_id in QUESTIONS_STORE:
        QUESTIONS_STORE[q_id]['relations'] = [
            rel for rel in QUESTIONS_STORE[q_id]['relations']
            if rel.get('target_id') != question_id
        ]
        QUESTION_GRAPH[q_id] = QUESTIONS_STORE[q_id]['relations']
    
    _save_data()
    print(f"✓ Pregunta {question_id} eliminada")
    return True

def get_question_by_id(question_id):
    """Obtiene una pregunta específica por ID."""
    _load_data()
    return QUESTIONS_STORE.get(question_id)

def get_total_questions():
    """Retorna el número total de preguntas."""
    _load_data()
    return len(QUESTIONS_STORE)

def get_next_id_number():
    """Retorna el próximo número de ID."""
    _load_data()
    return _NEXT_ID

# Cargar los datos al importar el módulo
_load_data()