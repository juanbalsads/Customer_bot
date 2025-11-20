# tests/test_answer.py

from typing import Dict, Any, List
import types

from bot import answer


# ==========================
# Fakes para el LLM
# ==========================

class FakeLLMOk:
    """Simula un LLM que responde de forma normal, sin pedir derivación a humano."""
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages):
        # Importante: NO usar frases que contengan
        # "derivar a un agente humano",
        # "no dispongo de suficiente información",
        # "no tengo suficiente información",
        # "no puedo responder con seguridad"
        texto_respuesta = (
            "Esta es una respuesta automática basada en la base de conocimiento. "
            "Dispongo de información suficiente para responder a tu consulta."
        )
        return types.SimpleNamespace(content=texto_respuesta)



class FakeLLMNeedsHuman:
    """Simula un LLM que indica falta de info y sugiere derivar a humano."""
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages):
        texto_respuesta = (
            "Con la información disponible no puedo responder con seguridad. "
            "Te recomiendo derivar a un agente humano para revisar este caso."
        )
        return types.SimpleNamespace(content=texto_respuesta)


# ==========================
# Tests de build_context_text
# ==========================

def test_build_context_text_no_hits():
    """
    Si no hay hits, debe devolver el mensaje de 'No hay información relevante...'.
    """
    ctx = answer.build_context_text([])
    assert "No hay información relevante" in ctx


def test_build_context_text_with_hits():
    """
    Si hay hits, debe concatenar líneas con formato:
    [categoria] pregunta_canonica: respuesta_base
    separadas por '\n'.
    """
    hits = [
        {
            "categoria": "shipping_policy",
            "pregunta_canonica": "¿Cuál es vuestra política de envíos?",
            "respuesta_base": "Enviamos en 24-48h.",
        },
        {
            "categoria": "return_policy",
            "pregunta_canonica": "¿Cuál es vuestra política de devoluciones?",
            "respuesta_base": "Puedes devolver en 30 días.",
        },
    ]

    ctx = answer.build_context_text(hits)
    lines = ctx.split("\n")
    assert len(lines) == 2
    assert lines[0].startswith("[shipping_policy]")
    assert "¿Cuál es vuestra política de envíos?" in lines[0]
    assert "Enviamos en 24-48h." in lines[0]


# ==========================
# Tests de answer_node
# ==========================

def test_answer_node_happy_path_no_revision(monkeypatch):
    """
    Caso feliz:
    - Hay intención y hits.
    - El LLM responde sin sugerir derivación a humano.
    Debe:
    - Rellenar state['answer'] con 'necesita_revision_humano' = False
    - Mantener el estado original sin mutar
    - Incluir num_hits e intencion_principal en metadata
    - Guardar answer_raw en debug
    """

    # Mock del prompt para no depender de prompt_store real
    def fake_get_prompt(key: str) -> str:
        assert key == "answer_agent.system"
        return "SYSTEM_PROMPT_FAKE"

    monkeypatch.setattr(answer, "get_prompt", fake_get_prompt)

    # Mock del LLM
    def fake_chat_openai(*args, **kwargs):
        return FakeLLMOk()

    monkeypatch.setattr(answer, "ChatOpenAI", fake_chat_openai)

    hits: List[Dict[str, Any]] = [
        {
            "categoria": "shipping_policy",
            "pregunta_canonica": "¿Cuál es vuestra política de envíos?",
            "respuesta_base": "Enviamos en 24-48h.",
            "score": 1.0,
        }
    ]

    state = {
        "user_message": "Quiero saber vuestra política de envíos.",
        "nlp": {
            "intent": {
                "tipo_mensaje": "pregunta",
                "intencion": "shipping_policy",
                "confianza": 0.9,
                "sentimiento": "neutral",
            },
            "entidades": [],
        },
        "knowledge_hits": hits,
        "answer": None,
        "debug": {},
    }

    original_state = dict(state)

    new_state = answer.answer_node(state)

    # 1) El estado original no se ha mutado
    assert state == original_state

    # 2) Se ha creado 'answer'
    assert "answer" in new_state
    ans = new_state["answer"]

    # 3) La respuesta es la del FakeLLMOk
    assert "respuesta" in ans
    assert "respuesta automática" in ans["respuesta"]
    assert ans["necesita_revision_humano"] is False
    assert ans["razon"] is None

    # 4) Metadata correcta
    assert ans["metadata"]["num_hits"] == 1
    assert ans["metadata"]["intencion_principal"] == "shipping_policy"

    # 5) Debug contiene 'answer_raw'
    assert "debug" in new_state
    assert "answer_raw" in new_state["debug"]
    assert new_state["debug"]["answer_raw"] == ans["respuesta"]


def test_answer_node_marks_necesita_revision_when_llm_says_so(monkeypatch):
    """
    Si el texto del LLM incluye expresiones como 'derivar a un agente humano'
    o 'no puedo responder con seguridad', debe marcar 'necesita_revision_humano' = True
    y rellenar 'razon'.
    """

    def fake_get_prompt(key: str) -> str:
        assert key == "answer_agent.system"
        return "SYSTEM_PROMPT_FAKE"

    monkeypatch.setattr(answer, "get_prompt", fake_get_prompt)

    def fake_chat_openai(*args, **kwargs):
        return FakeLLMNeedsHuman()

    monkeypatch.setattr(answer, "ChatOpenAI", fake_chat_openai)

    state = {
        "user_message": "Tengo una pregunta complicada.",
        "nlp": {
            "intent": {
                "tipo_mensaje": "pregunta",
                "intencion": "caso_complicado",
                "confianza": 0.6,
                "sentimiento": "neutral",
            },
            "entidades": [],
        },
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    new_state = answer.answer_node(state)

    ans = new_state["answer"]

    assert ans["necesita_revision_humano"] is True
    assert ans["razon"] is not None
    # El texto debe contener las frases del FakeLLMNeedsHuman
    assert "no puedo responder con seguridad" in ans["respuesta"].lower()
    assert "agente humano" in ans["respuesta"].lower()
    assert "answer_raw" in new_state["debug"]
    assert new_state["debug"]["answer_raw"] == ans["respuesta"]
