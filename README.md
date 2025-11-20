# Versión 1:

El usuario escribe un mensaje (por ejemplo:

> “Hola, quiero saber cuánto tardáis en enviar los pedidos a Canarias y si hay gastos de envío extra.”)

El sistema:

1. Llama a un **AgenteNLP (LLM)** → detecta intención, tipo de mensaje, sentimiento, entidades.
2. Llama a un **AgenteKnowledge** → busca en `faq.csv` la información relevante.
3. Llama a un **AgenteRespuesta (LLM)** → genera respuesta usando el contexto de FAQ.

Todo eso orquestado con **LangGraph**:

- Un grafo de estados con nodos: `nlp → knowledge → responder`.

Lo probarás con un **CLI** (programa en consola) donde escribes como cliente y ves:

- Intención detectada.
- Categorías de FAQ usadas.
- Respuesta del “agente”.


## Dejamos para más adelante:

- Base de datos SQLite.
- Prompts almacenados en BD.
- Router avanzado.
- Panel web.


## ¿Es `faq.csv` una forma de RAG?

Sí. En tu arquitectura, `faq.csv` funciona como una fuente de conocimiento para un sistema RAG simplificado. A continuación se detalla cómo encaja dentro del flujo.

### Qué es un RAG a alto nivel

Un sistema RAG (Retrieval-Augmented Generation) consta de dos fases:

1. Retrieval: búsqueda de información relevante en una base de conocimiento (documentos, FAQs, PDFs, bases de datos).
2. Augmented Generation: generación de una respuesta por parte de un LLM usando los fragmentos recuperados como contexto.

Normalmente, el retrieval se realiza mediante embeddings y bases vectoriales, pero en versiones iniciales puede hacerse con métodos más simples.

### Cómo encaja tu diseño en este esquema

Tu flujo:

1. AgenteNLP (LLM): detecta intención, tipo de mensaje, sentimiento y entidades. Esto corresponde a análisis de lenguaje, no a RAG.
2. AgenteKnowledge: busca en `faq.csv` la información relevante. Esta es la fase de retrieval. Según la implementación, puede ser:
   - Un RAG básico: búsqueda por palabras clave, categorías o coincidencia de texto.
   - Un RAG más avanzado: embeddings y búsqueda vectorial.
3. AgenteRespuesta (LLM): genera una respuesta utilizando el contexto obtenido del archivo CSV. Esto corresponde a la fase de augmented generation.

Con esta estructura, `faq.csv` + AgenteKnowledge + AgenteRespuesta constituyen un sistema RAG simplificado.

### Versión 1: RAG simplificado

En tu versión 1:

- `faq.csv` actúa como repositorio de conocimiento.
- El AgenteKnowledge realiza la búsqueda de las FAQs más relevantes.
- El AgenteRespuesta utiliza esa información para generar una respuesta fundamentada.

Este flujo reproduce el patrón básico de un sistema RAG, sin necesidad de una base vectorial ni embeddings.

### Cómo escalar a un RAG más avanzado

En versiones futuras puedes ampliar el sistema con:

1. Sustituir `faq.csv` por SQLite o un vector store.
2. Generar embeddings de cada FAQ.
3. Implementar búsqueda semántica tipo top-k.
4. Re-rank con LLM para seleccionar la FAQ más adecuada.
5. Integrar filtrado basado en la intención detectada por el AgenteNLP.

Esto permitirá pasar de un RAG básico a un RAG completamente semántico y escalable.



# Modelos de datos de estado: `bot/models.py` Pydantic

Queremos que el estado del grafo (lo que circula entre nodos) tenga una forma clara. 

Usaremos Pydantic:
- Permite definir "contratos" de datos muy claros. No son los agentes, tampoco son las lógica del sistema. Son las cajas con forma exacta donde cada agenta va a poner su parte de la información. 
- Si el LLM devuelve algo raro o falta un campo, Pydantic te lo hará notar.
- Luego puedes hacer `.model_dump()`para convertir a `dic` fácilmente.

### Analogía clara:
Imagina que se está construyendo una fábrica
- Tienes máquinas que hacen cosas distintas -> Agentes.
- Tienes cintas transportadoras que llevan piezas de una máquina a otra -> LangGraph.
- Tienes cajas con formas concretas donde cada máquina debe colocar el resultado -> Clases Pydantic. 
Gracias a Pydantic cada agente sabe exactamente qué tipo de documentos tiene que crear, es como una plantilla. 