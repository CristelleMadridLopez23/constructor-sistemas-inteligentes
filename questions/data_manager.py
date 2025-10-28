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

# Funciones para el sistema experto
def get_next_questions(current_question_id, answer, asked_questions=None):
    """
    Determina las siguientes preguntas basadas en la respuesta actual y el historial.
    Retorna una lista de IDs de preguntas ordenadas por peso y relación.
    """
    _load_data()
    if asked_questions is None:
        asked_questions = set()
    
    candidates = []
    
    # Si tenemos una pregunta actual, buscar relaciones directas primero
    if current_question_id and current_question_id in QUESTIONS_STORE:
        current = QUESTIONS_STORE[current_question_id]
        for relation in current.get('relations', []):
            if (relation['condition'] == answer and 
                relation['target_id'] not in asked_questions):
                # Dar prioridad extra a las relaciones directas
                weight = float(relation.get('weight', 0.5)) * 2
                candidates.append((
                    weight,
                    relation['target_id'],
                    True  # Marca que es una relación directa
                ))
    
    # Si no hay suficientes candidatos por relación directa, buscar por importancia
    if len(candidates) == 0:
        importance_weights = {'High': 0.9, 'Medium': 0.5, 'Low': 0.3}
        for qid, q in QUESTIONS_STORE.items():
            if qid not in asked_questions and qid not in [c[1] for c in candidates]:
                base_weight = importance_weights[q['importance']]
                
                # Buscar relaciones indirectas desde cualquier pregunta anterior
                indirect_weight = 0
                if current_question_id:
                    for prev_q in asked_questions:
                        if prev_q in QUESTIONS_STORE:
                            for rel in QUESTIONS_STORE[prev_q].get('relations', []):
                                if rel['target_id'] == qid:
                                    indirect_weight = max(indirect_weight, float(rel.get('weight', 0)) * 0.5)
                
                final_weight = max(base_weight, indirect_weight)
                candidates.append((
                    final_weight,
                    qid,
                    False  # No es una relación directa
                ))
    
    # Ordenar por peso (mayor a menor) y priorizar relaciones directas
    candidates.sort(key=lambda x: (not x[2], -x[0]))  # Primero por relación directa, luego por peso
    return [qid for _, qid, _ in candidates]

def build_decision_tree(answers):
    """
    Construye un árbol de decisión basado en las respuestas dadas.
    Retorna una estructura de datos representando el árbol.
    """
    tree = []
    prev_id = None
    
    for qid, answer in answers.items():
        question = QUESTIONS_STORE[qid]
        node = {
            'id': qid,
            'question': question['question'],
            'answer': answer,
            'children': []
        }
        
        # Buscar relaciones que llevaron a esta pregunta
        if prev_id:
            prev_question = QUESTIONS_STORE[prev_id]
            for rel in prev_question.get('relations', []):
                if rel['target_id'] == qid and rel['condition'] == answers[prev_id]:
                    node['weight'] = rel['weight']
                    break
        
        tree.append(node)
        prev_id = qid
    
    return tree

# Cargar los datos al importar el módulo
_load_data()