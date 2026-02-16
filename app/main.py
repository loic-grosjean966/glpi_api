from fastapi import FastAPI
from pydantic import BaseModel
from app.glpi.routes import router as glpi_router


class HealthResponse(BaseModel):
    """Réponse du contrôle de santé"""
    status: str

# Configuration de l'API
app = FastAPI(
    title="GLPI Integration API",
    description="""
API REST pour l'intégration avec **GLPI** (Gestionnaire Libre de Parc Informatique).

## Fonctionnalités

- **Session** : Test de connexion, session complète, configuration GLPI
- **Profils & Entités** : Gestion des profils utilisateur et entités accessibles
- **CRUD Items** : Lecture, création, mise à jour et suppression d'éléments GLPI
- **Recherche** : Moteur de recherche GLPI avec pagination et tri
- **Sous-éléments** : Accès aux éléments liés (logs, tickets, documents, etc.)

## Types d'éléments courants

| Type | Description |
|------|-------------|
| `Computer` | Ordinateurs |
| `User` | Utilisateurs |
| `Ticket` | Tickets / Incidents |
| `Printer` | Imprimantes |
| `Monitor` | Moniteurs |
| `Software` | Logiciels |
| `NetworkEquipment` | Équipements réseau |
| `Phone` | Téléphones |
| `Peripheral` | Périphériques |

## Authentification

L'API utilise un **App-Token** et un **User-Token** configurés dans le fichier `.env`.
Chaque requête ouvre et ferme automatiquement une session GLPI.
""",
    version="1.0.0",
    contact={
        "name": "Support API",
        "url": "https://github.com/votreorg/glpi-api",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Vérification de l'état et de la disponibilité de l'API",
        },
        {
            "name": "GLPI",
            "description": "Endpoints pour interagir avec GLPI : session, profils, entités, "
            "CRUD d'éléments (Computer, User, Ticket, etc.), recherche avancée et sous-éléments",
        },
        {
            "name": "User",
            "description": "Endpoints liés à la gestion des utilisateurs et de leurs profils",
        },
        {
            "name": "Item",
            "description": "Endpoints pour la gestion des éléments GLPI (Computer, Printer, etc.) "
            "et de leurs sous-éléments (logs, documents, etc.)",
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