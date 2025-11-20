# bot/models.py
from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    """
    Representa la intención inferida por el AgenteNLP.
    """
    tipo_mensaje: Literal["pregunta", "queja", "devolucion", "otro"]
    intencion: str
    confianza: float = Field(ge=0.0, le=1.0)
    sentimiento: Literal["positivo", "neutral", "negativo"]


class Entity(BaseModel):
    """
    Entidad extraída del mensaje (ej. lugar, producto, numero_pedido).
    """
    tipo: str
    valor: str


class NLPResult(BaseModel):
    """
    Resultado completo de la fase NLP.
    """
    intent: IntentResult
    #  importante: default_factory para listas
    entidades: List[Entity] = Field(default_factory=list)


class KnowledgeHit(BaseModel):
    """
    Representa una FAQ relevante encontrada por el AgenteKnowledge.
    """
    categoria: str
    pregunta_canonica: str
    respuesta_base: str
    score: float


class AnswerResult(BaseModel):
    """
    Respuesta generada por el AgenteRespuesta.
    """
    respuesta: str
    necesita_revision_humano: bool = False
    razon: Optional[str] = None
    #  default_factory para dict
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BotState(BaseModel):
    """
    Estado global que viaja a través del grafo de LangGraph.
    LangGraph puede usar este modelo directamente.
    """
    user_message: str
    nlp: Optional[NLPResult] = None
    # default_factory también aquí
    knowledge_hits: List[KnowledgeHit] = Field(default_factory=list)
    answer: Optional[AnswerResult] = None
    debug: Dict[str, Any] = Field(default_factory=dict)
