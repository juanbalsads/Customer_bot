from bot.graph import build_graph, initial_state
from pydantic import BaseModel
from loguru import logger
import json
def to_json_safe(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_safe(item) for item in obj]
    else:
        return obj





def main():
        logger.info("Inicio de la app")
        app = build_graph()
        print("Asistente CX - escribe 'salir' para terminar.\n")

        while True:
            msg = input("Cliente: ").strip()
            logger.debug("Mensaje recibido: {}", msg)

            if msg.lower() == "salir":
                break

            # Estado inicial como BotState
            state = initial_state(msg)
            logger.info(
                "Estado inicial:\n{}",
                state.model_dump_json(indent=4, ensure_ascii=False),
            )

            final_state = None

            # Ejecutamos el grafo paso a paso con LangGraph
            for step in app.stream(state):
                # step es un BotState después de cada nodo
                final_state = step
            
            
            print(type(final_state))
            print(json.dumps(to_json_safe(final_state), indent=4, ensure_ascii=False))

            break    


            """            
            if final_state is None:
                logger.error("No se obtuvo estado final del grafo.")
                print("Algo fue mal, no se obtuvo estado final.")
                continue

            logger.info(
                "Estado final del grafo:\n{}",
                #final_state.model_dump_json(indent=4, ensure_ascii=False),
            )

            # ==========================
            # Desempaquetar el estado
            # ==========================

            nlp = final_state.nlp
            hits = final_state.knowledge_hits or []
            answer = final_state.answer or {}

            # Intent y entidades (soportando que nlp pueda ser None)
            intent = getattr(nlp, "intent", None) if nlp else None
            entidades = getattr(nlp, "entidades", []) if nlp else []

            # Respuesta y flag de revisión humana
            respuesta = answer.get("respuesta", "") if isinstance(answer, dict) else ""
            needs_human = (
                answer.get("necesita_revision_humano", False)
                if isinstance(answer, dict)
                else False
            )

            # ==========================
            # DEBUG por consola
            # ==========================

            # Intent (como dict si es Pydantic)
            if intent is not None:
                try:
                    intent_debug = intent.model_dump()
                except AttributeError:
                    intent_debug = intent
            else:
                intent_debug = None

            # Entidades (lista de dicts si son modelos)
            entidades_debug = []
            for e in entidades:
                try:
                    entidades_debug.append(e.model_dump())
                except AttributeError:
                    entidades_debug.append(e)

            # Categorías de los hits (soportando dicts u objetos)
            categorias_hits = []
            for h in hits:
                if isinstance(h, dict):
                    categorias_hits.append(h.get("categoria"))
                else:
                    categorias_hits.append(getattr(h, "categoria", None))

            print("\n[DEBUG] INTENCIÓN:", intent_debug)
            print("[DEBUG] ENTIDADES:", entidades_debug)
            print("[DEBUG] HITS (categorías):", categorias_hits)

            print("\nAgente:", respuesta)
            if needs_human:
                print("⚠ Esta respuesta se marcaría para revisión humana.")
            print("-" * 60)
            
            """

        logger.info("Fin de la app")

    
    
        

if __name__ == "__main__":
    main()




"""  
#logger.info("Inicio de la app")
    app = build_graph()
    print("Asistente CX - escribe 'salir' para terminar.\n")

    while True:
        msg = input("Cliente: ").strip()
        logger.debug("Mensaje recibido: {}", msg)
        if msg.lower() == "salir":
            break
   
        
        bot_state = initial_state(msg) # Tipo BotState
        final_state = None
        logger.info("Estado inicial del nodo: \n{}", bot_state.model_dump_json(indent=4, ensure_ascii=False))
        

        # Ejecutar SOLO el nodo NLP
        new_state = nlp_node(bot_state)

        logger.info("\ntipo de data: {}\nEstado inicial del nodo: \n{}",type(new_state), new_state.model_dump_json(indent=4, ensure_ascii=False))

        # Ejecutar SOLO el nodo Knowledge
        new_state_knowledge = knowledge_node(new_state)

        logger.info("\ntipo de data: {}\nEstado del node despues de NODO knowledge: \n{}",type(new_state_knowledge), new_state_knowledge.model_dump_json(indent=4, ensure_ascii=False))

        # Ejecutar SOLO el nodo Answer
        final_state = answer_node(new_state_knowledge)

        logger.info("\ntipo de data: {}\nEstado del node despues de NODO knowledge: \n{}",type(final_state), final_state.model_dump_json(indent=4, ensure_ascii=False))
        
        break
    logger.info("Fin de la app")

"""  