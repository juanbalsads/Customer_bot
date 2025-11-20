# tests/test_nlp_agent.py
import json
import types

from bot import nlp_agent


# ==========================
# Fakes para el LLM
# ==========================

class FakeLLMGood:
    """Simula un LLM que devuelve JSON válido."""
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages):
        fake_response = {
            "intent": {
                "tipo_mensaje": "pregunta",
                "intencion": "shipping_policy",
                "confianza": 0.85,
                "sentimiento": "neutral",
            },
            "entidades": [
                {"tipo": "producto", "valor": "zapatillas"},
            ],
        }
        return types.SimpleNamespace(content=json.dumps(fake_response))


class FakeLLMBadJSON:
    """Simula un LLM que devuelve algo que NO es JSON."""
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages):
        return types.SimpleNamespace(content="esto NO es JSON")


# ==========================
# Tests
# ==========================

def test_nlp_node_happy_path(monkeypatch):
    """
    Caso 'feliz': el LLM devuelve JSON válido y nlp_node
    rellena correctamente el campo 'nlp' y 'debug["nlp_raw"]'.
    """

    def fake_chat_openai(*args, **kwargs):
        return FakeLLMGood()

    monkeypatch.setattr(nlp_agent, "ChatOpenAI", fake_chat_openai)

    state = {
        "user_message": "Quiero saber vuestra política de envíos para zapatillas.",
        "nlp": None,
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    # Guardamos una copia para comprobar que no se muta el estado original
    original_state = dict(state)

    new_state = nlp_agent.nlp_node(state)

    # 1) El estado original no se ha cambiado
    assert state == original_state

    # 2) Se ha añadido la clave 'nlp'
    assert "nlp" in new_state

    # 3) Comprobamos contenido del intent
    intent = new_state["nlp"]["intent"]
    assert intent["tipo_mensaje"] == "pregunta"
    assert intent["intencion"] == "shipping_policy"
    assert intent["confianza"] == 0.85
    assert intent["sentimiento"] == "neutral"

    # 4) Entidades
    entidades = new_state["nlp"]["entidades"]
    assert len(entidades) == 1
    assert entidades[0]["tipo"] == "producto"
    assert entidades[0]["valor"] == "zapatillas"

    # 5) Debug: nlp_raw existe y es JSON parseable
    assert "debug" in new_state
    assert "nlp_raw" in new_state["debug"]
    raw = new_state["debug"]["nlp_raw"]
    parsed = json.loads(raw)
    assert parsed["intent"]["intencion"] == "shipping_policy"


def test_nlp_node_fallback_when_json_invalid(monkeypatch):
    """
    Si el LLM devuelve un JSON inválido, nlp_node debe usar el fallback
    con tipo_mensaje='otro', intencion='unknown', sentimiento='neutral'
    y entidades vacías.
    """

    def fake_chat_openai(*args, **kwargs):
        return FakeLLMBadJSON()

    monkeypatch.setattr(nlp_agent, "ChatOpenAI", fake_chat_openai)

    state = {
        "user_message": "Mensaje cualquiera.",
        "nlp": None,
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    new_state = nlp_agent.nlp_node(state)

    intent = new_state["nlp"]["intent"]
    assert intent["tipo_mensaje"] == "otro"
    assert intent["intencion"] == "unknown"
    assert intent["sentimiento"] == "neutral"
    assert intent["confianza"] == 0.0
    assert new_state["nlp"]["entidades"] == []


def test_nlp_node_uses_correct_prompt_key(monkeypatch):
    """
    Comprobamos que nlp_node pide el prompt 'nlp_agent.system'
    a través de get_prompt.
    """
    called_keys = []

    def fake_get_prompt(key: str) -> str:
        called_keys.append(key)
        return "PROMPT_FAKE"

    # Mock de get_prompt
    monkeypatch.setattr(nlp_agent, "get_prompt", fake_get_prompt)

    # Mock del LLM para no llamar a OpenAI
    def fake_chat_openai(*args, **kwargs):
        return FakeLLMGood()

    monkeypatch.setattr(nlp_agent, "ChatOpenAI", fake_chat_openai)

    state = {
        "user_message": "Hola, quiero hacer una consulta.",
        "nlp": None,
        "knowledge_hits": [],
        "answer": None,
        "debug": {},
    }

    _ = nlp_agent.nlp_node(state)

    # Comprobamos que se ha llamado con la clave correcta
    assert "nlp_agent.system" in called_keys
