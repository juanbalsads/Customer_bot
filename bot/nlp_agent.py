import json
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from bot.models import BotState, NLPResult
from bot.config import OPENAI_MODEL_NAME, OPENAI_API_KEY
from bot.prompt_store import get_prompt

# Los nodos de los agentes siempre reciben siempre BotState, que recordemos tiene. Estado global que viaja a través del grafo de LangGraph. user_message, nlp, knowledge_hits, answer, debug





def nlp_node(bot_state: BotState) -> BotState:

    user_message = bot_state.user_message


    system_prompt = get_prompt("nlp_agent.system")

    # Creamos el LLM de LangChain (ChatOpenAI)
    try:
        llm = ChatOpenAI(
            model=OPENAI_MODEL_NAME,
            temperature=0,
            api_key=OPENAI_API_KEY,
        )
        logger.info("Conexión con OpenAI inicializada correctamente. Modelo: {}", OPENAI_MODEL_NAME)
    except Exception as e:
        logger.error("Error al inicializar la conexión con OpenAI: {}", e)
        raise

    # Realizamos la llamada al modelo
    try:
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
        )
        raw = response.content
        logger.info("Petición a OpenAI realizada correctamente. Respuesta recibida.")
    except Exception as e:
        logger.error("Error al invocar el modelo OpenAI: {}", e)
        raise

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "intent": {
                "tipo_mensaje": "otro",
                "intencion": "unknown",
                "confianza": 0.0,
                "sentimiento": "neutral",
            },
            "entidades": [],
        }

    # Para construir un nuevo estado serializable que LangGraph pueda manejar.

    # new_state: BotState → sólo indica al IDE “esta variable debería tener esta estructura”, pero no convierte nada.
    # dict(bot_state) → convierte el modelo Pydantic BotState en un diccionario plano de Python.
    new_state = bot_state.model_copy()


    # Guardar NLPResult
    new_state.nlp = NLPResult(**data)

    # Actualizar debug
    debug = new_state.debug.copy()
    debug["nlp_raw"] = raw
    new_state.debug = debug

    return new_state

