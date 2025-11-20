# Centralizas la configuración en un solo lugar. 
# Si mañaña se cmabia el modelo, solo tocas .env

from dotenv import load_dotenv
import os

# Carga las variables de entorno del archivo .env

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-4.1-mini") # Es un fall-back (valor por defecto) por si olvidas definirlo en .env. Si en .env está definido, ese valor siempre gana.
FAQ_CSV_PATH = os.environ.get("FAQ_CSV_PATH", "data/faq.csv")
PROMPTS_DB_PATH = os.environ.get("PROMPTS_DB_PATH", "data/prompts.json")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY no está definida. Añádela en el archivo .env.")
