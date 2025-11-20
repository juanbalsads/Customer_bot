# tests/test_knowledge.py

import types

from bot import knowledge


# ==========================
# Tests de simple_match_score
# ==========================

def test_simple_match_score_strong_match_contenido():
    """
    Debe devolver 1.0 cuando la categoría está contenida en la intención
    o la intención en la categoría.
    """
    score1 = knowledge.simple_match_score("shipping_policy", "shipping")
    score2 = knowledge.simple_match_score("shipping", "shipping_policy")
    score3 = knowledge.simple_match_score("shipping_policy", "shipping_policy")

    assert score1 == 1.0
    assert score2 == 1.0
    assert score3 == 1.0


def test_simple_match_score_weak_match_tokens():
    """
    Debe devolver 0.3 cuando comparten algún token de la categoría
    separado por guiones bajos.
    """
    # categoria: "devolucion_producto" → tokens: ["devolucion", "producto"]
    score = knowledge.simple_match_score("quiero saber la devolucion", "devolucion_producto")
    assert score == 0.3


def test_simple_match_score_no_match():
    """
    Debe devolver 0.0 cuando no hay coincidencias relevantes.
    """
    score = knowledge.simple_match_score("politica_de_envios", "horario_tienda")
    assert score == 0.0

    # También si intencion está vacío o None
    assert knowledge.simple_match_score("", "shipping") == 0.0
    assert knowledge.simple_match_score(None, "shipping") == 0.0


# ==========================
# Tests de knowledge_node
# ==========================

def test_knowledge_node_happy_path(monkeypatch):
    """
    Caso feliz: hay intención detectada y el CSV (mockeado) contiene
    varias filas. knowledge_node debe:
    - Calcular scores
    - Ordenarlos de mayor a menor
    - Devolver sólo los top 3 en 'knowledge_hits'
    - No mutar el estado original
    """

    # Fake de FAQ: 4 entradas, con categorías que matchean de forma diferente
    fake_faq_rows = [
        {
            "categoria": "shipping_policy",
            "pregunta_canonica": "¿Cuál es vuestra política de envíos?",
            "respuesta_base": "Nuestra política de envíos es la siguiente...",
        },
        {
            "categoria": "shipping_delays",
            "pregunta_canonica": "¿Por qué mi pedido se retrasa?",
            "respuesta_base": "A veces hay retrasos por...",
        },
        {
            "categoria": "return_policy",
            "pregunta_canonica": "¿Cómo puedo devolver un producto?",
            "respuesta_base": "Nuestra política de devoluciones es...",
        },
        {
            "categoria": "tienda_fisica",
            "pregunta_canonica": "¿Tenéis tienda física?",
            "respuesta_base": "Sí, tenemos tienda en...",
        },
    ]

    # Mock de load_faq para que no lea de disco
    def fake_load_faq():
        return fake_faq_rows

    monkeypatch.setattr(knowledge, "load_faq", fake_load_faq)

    state = {
        "user_message": "Quiero saber vuestra política de envíos",
        "nlp": {
            "intent": {
                "tipo_mensaje": "pregunta",
                "intencion": "shipping_policy",
                "confianza": 0.9,
                "sentimiento": "neutral",
            },
            "entidades": [],
        },
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    original_state = dict(state)

    new_state = knowledge.knowledge_node(state)

    # 1) El estado original no se ha mutado
    assert state == original_state

    # 2) Se ha generado 'knowledge_hits'
    assert "knowledge_hits" in new_state
    hits = new_state["knowledge_hits"]

    # 3) Hay como máximo 3 resultados
    assert len(hits) <= 3

    # 4) El primer resultado debe ser la categoría con mejor match ("shipping_policy")
    assert hits[0]["categoria"] == "shipping_policy"
    assert hits[0]["pregunta_canonica"] == "¿Cuál es vuestra política de envíos?"
    assert hits[0]["respuesta_base"].startswith("Nuestra política de envíos")

    # 5) El campo 'score' existe
    assert "score" in hits[0]
    assert hits[0]["score"] > 0

    # 6) Debug debe contener 'knowledge_hits'
    assert "debug" in new_state
    assert "knowledge_hits" in new_state["debug"]
    assert new_state["debug"]["knowledge_hits"] == hits


def test_knowledge_node_no_intent_produces_empty_hits(monkeypatch):
    """
    Si no hay intención (o viene vacía), no debe haber resultados
    en 'knowledge_hits'.
    """

    # Aunque haya filas en FAQ, si la intención está vacía, score = 0.0
    fake_faq_rows = [
        {
            "categoria": "shipping_policy",
            "pregunta_canonica": "¿Cuál es vuestra política de envíos?",
            "respuesta_base": "Nuestra política de envíos es la siguiente...",
        }
    ]

    def fake_load_faq():
        return fake_faq_rows

    monkeypatch.setattr(knowledge, "load_faq", fake_load_faq)

    # Estado sin nlp o con intención vacía
    state = {
        "user_message": "Mensaje genérico",
        "nlp": {
            "intent": {
                "tipo_mensaje": "otro",
                "intencion": "",
                "confianza": 0.0,
                "sentimiento": "neutral",
            },
            "entidades": [],
        },
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    new_state = knowledge.knowledge_node(state)

    assert new_state["knowledge_hits"] == []
    assert new_state["debug"]["knowledge_hits"] == []


def test_knowledge_node_handles_missing_nlp_gracefully(monkeypatch):
    """
    Si el estado no tiene 'nlp' o viene como None,
    knowledge_node no debe romper y debe devolver hits vacíos.
    """

    def fake_load_faq():
        return [
            {
                "categoria": "shipping_policy",
                "pregunta_canonica": "¿Cuál es vuestra política de envíos?",
                "respuesta_base": "Nuestra política de envíos es la siguiente...",
            }
        ]

    monkeypatch.setattr(knowledge, "load_faq", fake_load_faq)

    state = {
        "user_message": "Mensaje sin análisis NLP",
        "nlp": None,
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    new_state = knowledge.knowledge_node(state)

    assert new_state["knowledge_hits"] == []
    assert new_state["debug"]["knowledge_hits"] == []
