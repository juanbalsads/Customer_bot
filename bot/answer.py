# bot/answer.py

from typing import List, Dict, Any
import json
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from bot.models import BotState
from bot.config import OPENAI_MODEL_NAME, OPENAI_API_KEY
from bot.prompt_store import get_prompt


def build_context_text(hits: List[Dict[str, Any]]) -> str:
    """
    Construye un texto de contexto a partir de la lista de FAQs relevantes.

    Este texto se le pasa al LLM para que se 'alimente' solo de esto.
    """
    if not hits:
        return "No hay información relevante en la base de conocimiento."

    ctx_lines = []

    for hit in hits:
        # Caso 1: dict
        if isinstance(hit, dict):
            categoria = hit.get("categoria", "")
            pregunta = hit.get("pregunta_canonica", "")
            respuesta = hit.get("respuesta_base", "")
        else:
            # Caso 2: modelo Pydantic o dataclass (KnowledgeHit, etc.)
            categoria = getattr(hit, "categoria", "")
            pregunta = getattr(hit, "pregunta_canonica", "")
            respuesta = getattr(hit, "respuesta_base", "")

        linea = f"[{categoria}] {pregunta}: {respuesta}"
        ctx_lines.append(linea)

    return "\n".join(ctx_lines)


def answer_node(state: BotState) -> BotState:
    """
    Nodo de LangGraph que genera la respuesta final al cliente.

    Usa:
      - state['user_message']
      - state['nlp']
      - state['knowledge_hits']

    Y añade:
      - state['answer'] (diccionario con la respuesta y metadatos)
    """
    logger.info("Ejecutando answer_node...")
    user_message = state.user_message
    nlp = state.nlp
    hits = state.knowledge_hits

    system_prompt = get_prompt("answer_agent.system")



    logger.info("Generando contexto...")
    contexto = build_context_text(hits)

    # Para inspección / depuración, a veces es útil tener el NLP en JSON plano
    nlp_json = nlp.model_dump_json(indent=4, ensure_ascii=False)

    user_prompt = f"""
MENSAJE DEL CLIENTE:
{user_message}

INTENCIÓN DETECTADA (JSON):
{nlp_json}

BASE DE CONOCIMIENTO:
{contexto}

INSTRUCCIONES:
- Responde al cliente usando SOLO la información de BASE DE CONOCIMIENTO.
- Si falta información para responder con seguridad, dilo claramente y sugiere derivar el caso a un agente humano.
- No inventes políticas, plazos ni condiciones que no estén en el contexto.
- Mantén un tono profesional, cercano y claro.
"""

    llm = ChatOpenAI(
        model=OPENAI_MODEL_NAME,
        temperature=0,
        api_key=OPENAI_API_KEY,
    )

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    respuesta_texto = response.content
    lower = respuesta_texto.lower()

    # Heurística muy simple para decidir si hay que derivar a un humano
    necesita_revision = (
        "derivar a un agente humano" in lower
        or "no dispongo de suficiente información" in lower
        or "no tengo suficiente información" in lower
        or "no puedo responder con seguridad" in lower
    )

    answer_dict: Dict[str, Any] = {
        "respuesta": respuesta_texto,
        "necesita_revision_humano": necesita_revision,
        "razon": "El modelo indica falta de información o necesidad de derivar a humano"
        if necesita_revision
        else None,
        "metadata": {
            "num_hits": len(hits),
            # Podrías añadir más cosas, por ejemplo la intención principal:
            "intencion_principal": nlp.intent,
        },
    }

    # Actualizamos el estado
    new_state = state.model_copy()

    new_state.answer = answer_dict

    # Debug seguro (copia completa)
    debug = new_state.debug.copy()
    debug["answer_raw"] = respuesta_texto
    new_state.debug = debug

    logger.info("answer_node finalizado correctamente.")

    return new_state
