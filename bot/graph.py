# bot/graph.py
from langgraph.graph import StateGraph, END
from bot.models import BotState  # lo puedes seguir usando para tipos internos si quieres
from bot.nlp_agent import nlp_node
from bot.knowledge import knowledge_node
from bot.answer import answer_node  # o como lo llames


def initial_state(user_message: str) -> BotState:
    """
    Estado inicial que se le pasa al grafo.
    Trabajamos con dict como esquema de estado en LangGraph.
    """
    return BotState(
        user_message=user_message,
        nlp = None,
        knowledge_hits=[],
        answer=None,
        debug={}
    )


def build_graph():
    #  El estado base del grafo es un dict
    graph = StateGraph(BotState)

    graph.add_node("nlp", nlp_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("nlp")
    graph.add_edge("nlp", "knowledge")
    graph.add_edge("knowledge", "answer")
    graph.add_edge("answer", END)

    return graph.compile()
