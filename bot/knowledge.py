# bot/knowledge.py

import csv
from typing import List, Dict, Any

from bot.config import FAQ_CSV_PATH
from bot.models import BotState  # aunque lo uses como dict, viene bien para el IDE
from loguru import logger


# Pequeña caché en memoria para no leer el CSV todo el rato
FAQ_CACHE: List[Dict[str, Any]] = []


def load_faq() -> List[Dict[str, Any]]:
    """
    Carga el CSV de FAQ una única vez y lo deja en memoria.

    Así no estamos abriendo el archivo en cada llamada al nodo.
    """
    global FAQ_CACHE
    if FAQ_CACHE:
        logger.debug("FAQ_CACHE ya cargada en memoria ({} filas).", len(FAQ_CACHE))
        return FAQ_CACHE

    logger.info("Cargando FAQ desde CSV: {}", FAQ_CSV_PATH)
    
    rows: List[Dict[str, Any]] = []

    try:
        with open(FAQ_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        logger.error("Error al leer FAQ_CSV_PATH ({}): {}", FAQ_CSV_PATH, e)
        raise

    FAQ_CACHE = rows
    logger.info("FAQ cargada correctamente: {} filas", len(rows))

    return FAQ_CACHE


def simple_match_score(intencion: str, categoria: str) -> float:
    """
    Heurística muy simple para medir la similitud entre:
    - la intención detectada por el AgenteNLP
    - la categoría de la FAQ

    La idea es: cuanto más se parezca el texto, mayor score.
    Puedes mejorar esto el día de mañana (embeddings, etc.).
    """
    intencion = (intencion or "").lower()
    categoria = (categoria or "").lower()

    if not intencion or not categoria:
        return 0.0

    # Coincidencia fuerte si uno contiene al otro
    if categoria in intencion or intencion in categoria:
        return 1.0

    int_tokens = set(intencion.split())
    cat_tokens = set(categoria.split())
    # Coincidencia débil si comparten alguna palabra
    inter = int_tokens & cat_tokens
    if inter:
        # Proporción de palabras en común
        return len(inter) / len(cat_tokens)

    return 0.0


def knowledge_node(state: BotState) -> BotState:
    """
    Nodo de LangGraph que:
    - Lee la intención desde state["nlp"]
    - Busca en faq.csv las filas más relevantes
    - Mete el resultado en state["knowledge_hits"]
    """

    logger.info("Ejecutando knowledge_node...")

    # 1) Cargar FAQ de disco o de caché
    faq_rows = load_faq()
    print(f"\nTotal filas cargadas: {len(faq_rows)}\n")

    # 2) Recuperar intención
    if state.nlp is None:
        logger.warning("No se encontró NLP en el estado, usando cadena vacía.")
        intencion = ""
    else:
        intencion = state.nlp.intent.intencion
        logger.debug("Intención detectada: '{}'", intencion)

    # 3) Calcular hits
    hits: List[Dict[str, Any]] = []

    for row in faq_rows:
        categoria = row.get("categoria", "")
        score = simple_match_score(intencion, categoria)
        if score > 0:
            logger.debug("Match: categoria='{}' ,  score={}", categoria, score)
            hits.append(
                {
                    "categoria": categoria,
                    "pregunta_canonica": row.get("pregunta_canonica", ""),
                    "respuesta_base": row.get("respuesta_base", ""),
                    "score": score,
                }
            )

    # Ordenamos de mayor a menor score y nos quedamos con los 3 mejores
    hits.sort(key=lambda h: h["score"], reverse=True)
    top_hits = hits[:3]
    logger.info("Total hits encontrados: {}. Top 3: {}", len(hits), top_hits)



    # 4) Actualizar el estado
    new_state = state.model_copy()
    new_state.knowledge_hits = top_hits

    # Debug seguro (copia del dict)
    debug = new_state.debug.copy()
    debug["knowledge_hits"] = top_hits
    new_state.debug = debug

    logger.info("knowledge_node finalizado correctamente.")

    return new_state
