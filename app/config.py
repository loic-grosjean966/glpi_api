import os
from dotenv import load_dotenv

load_dotenv()

GLPI_API_URL = os.getenv("GLPI_API_URL")
GLPI_APP_TOKEN = os.getenv("GLPI_APP_TOKEN")
GLPI_USER_TOKEN = os.getenv("GLPI_USER_TOKEN")

if not all([GLPI_API_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN]):
    raise ValueError(
        "Variables d'environnement manquantes. "
        "Vérifiez que GLPI_API_URL, GLPI_APP_TOKEN et GLPI_USER_TOKEN sont définis dans .env"
    )
