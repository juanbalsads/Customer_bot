# tests/test_graph.py

import types
from bot import graph


# ===========================================
# Fakes para los nodos del grafo
# ===========================================

def fake_nlp_node(state):
    """Simula que el nodo NLP añade un valor a state['nlp']."""
    new_state = dict(state)
    new_state["nlp"] = {"intent": {"intencion": "fake_intent"}}
    new_state["debug"] = dict(new_state.get("debug", {}))
    new_state["debug"]["nlp_node_called"] = True
    return new_state


def fake_knowledge_node(state):
    """Simula que el nodo Knowledge añade un hit."""
    new_state = dict(state)
    new_state["knowledge_hits"] = [
        {"categoria": "fake_category", "score": 1.0}
    ]
    new_state["debug"] = dict(new_state.get("debug", {}))
    new_state["debug"]["knowledge_node_called"] = True
    return new_state


def fake_answer_node(state):
    """Simula que el nodo Answer genera una respuesta final."""
    new_state = dict(state)
    new_state["answer"] = {"respuesta": "Fake answer", "necesita_revision_humano": False}
    new_state["debug"] = dict(new_state.get("debug", {}))
    new_state["debug"]["answer_node_called"] = True
    return new_state


# ===========================================
# Tests
# ===========================================

def test_initial_state_structure():
    """
    Verifica que initial_state construye correctamente el estado inicial.
    """
    user_message = "Hola"
    state = graph.initial_state(user_message)

    assert state["user_message"] == "Hola"
    assert state["nlp"] is None
    assert state["knowledge_hits"] == []
    assert state["answer"] is None
    assert isinstance(state["debug"], dict)


def test_graph_execution_order(monkeypatch):
    """
    Verifica que el grafo ejecuta los nodos en el orden correcto:

        nlp → knowledge → answer → END

    usando fakes para no depender de la lógica real.
    """

    # Mock de los nodos
    monkeypatch.setattr(graph, "nlp_node", fake_nlp_node)
    monkeypatch.setattr(graph, "knowledge_node", fake_knowledge_node)
    monkeypatch.setattr(graph, "answer_node", fake_answer_node)

    # Construimos el grafo con los fakes
    compiled_graph = graph.build_graph()

    # Estado inicial
    state = graph.initial_state("Mensaje de prueba")

    # Ejecutar todo el grafo
    final_state = compiled_graph.invoke(state)

    # =========================
    # Validaciones:
    # =========================

    # Orden de ejecución:
    assert final_state["debug"]["nlp_node_called"] is True
    assert final_state["debug"]["knowledge_node_called"] is True
    assert final_state["debug"]["answer_node_called"] is True

    # NLP node → modifica nlp
    assert final_state["nlp"] == {"intent": {"intencion": "fake_intent"}}

    # Knowledge node → añade hits
    assert final_state["knowledge_hits"] == [
        {"categoria": "fake_category", "score": 1.0}
    ]

    # Answer node → respuesta final
    assert final_state["answer"]["respuesta"] == "Fake answer"
    assert final_state["answer"]["necesita_revision_humano"] is False

    # Grafo debe devolver un estado funcional
    assert isinstance(final_state, dict)
    assert final_state["user_message"] == "Mensaje de prueba"
