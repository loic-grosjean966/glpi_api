from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from app.glpi.routes import router as glpi_router

# Modèles de réponse
class HealthResponse(BaseModel):
    """Réponse du contrôle de santé"""
    status: str

class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    status: str
    message: str

# Configuration de l'API
app = FastAPI(
    title="GLPI Integration API",
    description="API complète pour l'intégration et la gestion de GLPI. Permet d'accéder aux ressources GLPI (ordinateurs, utilisateurs, incidents, etc.) via une interface REST.",
    version="1.0.0",
    contact={
        "name": "Support API",
        "url": "https://github.com/votreorg/glpi-api",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Endpoints pour vérifier l'état et la disponibilité de l'API"
        },
        {
            "name": "GLPI",
            "description": "Endpoints pour interagir avec GLPI (récupération de données, gestion des ressources)"
        }
    ]
)

app.include_router(glpi_router)

@app.get(
    "/health",
    tags=["Health"],
    summary="Vérifier l'état de l'API",
    description="Endpoint pour vérifier si l'API est disponible et fonctionnelle",
    response_model=HealthResponse,
    responses={
        200: {"description": "API opérationnelle"}
    }
)
def health():
    """
    Vérifier l'état de l'API.
    
    **Retourne :**
    - `status`: État de l'API ("ok" si fonctionnelle)
    """
    return {"status": "ok"}