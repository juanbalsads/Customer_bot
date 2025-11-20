# Paso 0 – Estructura de carpetas

En tu carpeta de proyectos, crea:

```bash
mkdir customer_bot
cd customer_bot

mkdir bot
mkdir data
Estructura objetivo de esta versión:
arduino
Copiar código
customer_bot/
├─ .env
├─ requirements.txt
├─ data/
│  └─ faq.csv
├─ bot/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ models.py
│  ├─ nlp_agent.py
│  ├─ knowledge.py
│  ├─ responder.py
│  └─ graph.py
└─ main.py
Iremos archivo por archivo.

Paso 1 – Entorno virtual e instalación de dependencias
1.1 Crear entorno virtual
Esto sirve para que las dependencias de este proyecto no contaminen el resto de tu sistema.

bash
Copiar código
# Desde la carpeta customer_bot
python -m venv .venv

# Activar entorno:
# En Linux/Mac:
source .venv/bin/activate

# En Windows (PowerShell):
# .venv\Scripts\Activate.ps1
Verás que el prompt cambia (algo tipo (.venv) delante).

1.2 Crear requirements.txt
Crea el archivo requirements.txt en la raíz (customer_bot/) con este contenido:

Copiar código
python-dotenv
langchain
langchain-openai
langgraph
openai
Nota:
langchain-openai es el “conector” de LangChain con la API de OpenAI.
langgraph es el framework para orquestar agentes como un grafo.

Instala las dependencias:

bash
Copiar código
pip install --upgrade pip
pip install -r requirements.txt
Copiar código
