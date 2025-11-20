# bot/prompt_store.py
import json
from pathlib import Path
from functools import lru_cache

from bot.config import PROMPTS_DB_PATH


@lru_cache
def _load_prompts() -> dict:
    """
    Carga todos los prompts desde el fichero JSON.
    Se cachea en memoria para no leer disco en cada llamada.
    """
    path = Path(PROMPTS_DB_PATH)
    if not path.exists():
        raise RuntimeError(f"No se encontró el fichero de prompts en {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_prompt(key: str) -> str:
    """
    Devuelve el prompt asociado a una clave dada.
    Ej: "nlp_agent.system"
    """
    prompts = _load_prompts()
    try:
        return prompts[key]
    except KeyError:
        raise KeyError(
            f"No existe un prompt con clave '{key}' en {PROMPTS_DB_PATH}"
        )
