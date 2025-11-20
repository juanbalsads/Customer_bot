# tests/test_main.py

from typing import Dict, Any
import builtins

import main  # Ajusta este import si tu archivo se llama distinto (p.ej. bot_cli)


# ==========================
# Fakes para el grafo
# ==========================

class FakeAppNoRevision:
    """Grafo fake que devuelve un único estado final sin necesidad de revisión humana."""
    def stream(self, state: Dict[str, Any]):
        final_state = dict(state)
        final_state["nlp"] = {"intent": {"intencion": "fake_intent"}}
        final_state["knowledge_hits"] = [{"categoria": "fake_category", "score": 1.0}]
        final_state["answer"] = {
            "respuesta": "Respuesta fake sin necesidad de revisión.",
            "necesita_revision_humano": False,
        }
        final_state["debug"] = dict(final_state.get("debug", {}))
        final_state["debug"]["fake_app"] = True
        # Simulamos el comportamiento de app.stream: ir yielding estados
        yield final_state


class FakeAppWithRevision:
    """Grafo fake que devuelve un estado final que sí requiere revisión humana."""
    def stream(self, state: Dict[str, Any]):
        final_state = dict(state)
        final_state["nlp"] = {"intent": {"intencion": "fake_intent_revision"}}
        final_state["knowledge_hits"] = [{"categoria": "otra_categoria", "score": 1.0}]
        final_state["answer"] = {
            "respuesta": "Respuesta fake que sugiere derivar a un agente humano.",
            "necesita_revision_humano": True,
        }
        final_state["debug"] = dict(final_state.get("debug", {}))
        final_state["debug"]["fake_app_revision"] = True
        yield final_state


# ==========================
# Tests
# ==========================

def test_main_exits_on_salir(monkeypatch, capsys):
    """
    Verifica que el programa sale correctamente cuando el usuario escribe 'salir'
    en la primera interacción (sin llegar a llamar a build_graph).
    """

    # Simulamos que el usuario teclea solo 'salir'
    inputs = iter(["salir"])

    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    # No hace falta mockear build_graph porque nunca se llega a usar
    main.main()

    captured = capsys.readouterr()
    # Debe mostrar el mensaje de bienvenida
    assert "Asistente CX - escribe 'salir' para terminar." in captured.out


def test_main_happy_path_without_revision(monkeypatch, capsys):
    """
    Caso feliz:
    - El usuario envía un mensaje y luego 'salir'.
    - El grafo fake devuelve un estado final con:
        - nlp relleno
        - knowledge_hits relleno
        - answer con necesita_revision_humano = False
    Verificamos que:
        - Se imprimen los debug de NLP y HITS
        - Se imprime la respuesta del agente
        - NO se imprime el mensaje de 'marcar para revisión humana'
    """

    # 1) Mock de build_graph para que use FakeAppNoRevision
    def fake_build_graph():
        return FakeAppNoRevision()

    monkeypatch.setattr(main, "build_graph", fake_build_graph)

    # 2) Mock de input: primer mensaje del cliente, luego 'salir'
    inputs = iter(["Hola, quiero preguntar algo.", "salir"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    # 3) Ejecutar main
    main.main()

    # 4) Capturar salida
    captured = capsys.readouterr()
    out = captured.out

    # 5) Asserts sobre la salida
    assert "Asistente CX - escribe 'salir' para terminar." in out
    assert "[DEBUG] NLP:" in out
    assert "[DEBUG] HITS:" in out
    assert "fake_intent" in out            # viene del NLP fake
    assert "fake_category" in out          # viene de knowledge_hits
    assert "Respuesta fake sin necesidad de revisión." in out
    assert "Esta respuesta se marcaría para revisión humana." not in out


def test_main_path_with_revision(monkeypatch, capsys):
    """
    Caso en el que la respuesta se marca para revisión humana:
    - El grafo fake devuelve 'necesita_revision_humano' = True.
    Verificamos que se imprime el aviso correspondiente.
    """

    def fake_build_graph():
        return FakeAppWithRevision()

    monkeypatch.setattr(main, "build_graph", fake_build_graph)

    inputs = iter(["Mensaje que requiere revisión.", "salir"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    main.main()

    captured = capsys.readouterr()
    out = captured.out

    assert "Respuesta fake que sugiere derivar a un agente humano." in out
    assert "Esta respuesta se marcaría para revisión humana." in out

