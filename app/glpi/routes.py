from fastapi import APIRouter, Query, Path, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.glpi.client import GLPIClient

# Modèles de réponse
class SessionInfo(BaseModel):
    """Informations de session GLPI"""
    session_id: Optional[str] = None
    status: str

class ProfileInfo(BaseModel):
    """Profil utilisateur GLPI"""
    id: int
    name: str
    email: Optional[str] = None

class GLPITestResponse(BaseModel):
    """Réponse du test de connexion GLPI"""
    session: SessionInfo
    profile: ProfileInfo

class ItemsResponse(BaseModel):
    """Réponse contenant une liste d'éléments GLPI"""
    status: str
    data: List[Dict[str, Any]]
    count: Optional[int] = None

router = APIRouter(prefix="/glpi", tags=["GLPI"])

@router.get(
    "/test",
    summary="Tester la connexion à GLPI",
    description="Teste la connexion au serveur GLPI et récupère les informations de session et de profil utilisateur",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Connexion réussie - session et profil récupérés"},
        500: {"description": "Erreur de connexion au serveur GLPI"}
    }
)
def test_glpi_connection():
    """
    Test la connexion au serveur GLPI.
    
    **Fonctionnalités :**
    - Initialise une session de connexion
    - Récupère les informations du profil utilisateur
    
    **Retourne :**
    - `session`: Informations de session (ID, statut)
    - `profile`: Données du profil utilisateur
    
    **Exceptions :**
    - 500: Erreur lors de la connexion ou de l'initialisation
    """
    try:
        client = GLPIClient()
        session = client.init_session()
        profile = client.get_my_profile()

        return {
            "session": session,
            "profile": profile,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion GLPI: {str(e)}"
        )

@router.get(
    "/items/{item_type}",
    summary="Récupérer les éléments GLPI",
    description="Récupère une liste d'éléments du type spécifié depuis GLPI (Computers, Users, Incidents, etc.)",
    response_model=ItemsResponse,
    responses={
        200: {"description": "Liste d'éléments récupérée avec succès"},
        404: {"description": "Type d'élément non trouvé"},
        500: {"description": "Erreur serveur lors de la récupération"}
    }
)
def get_items(
    item_type: str = Path(..., description="Type d'élément à récupérer (ex: Computer, User, Ticket)"),
    limit: Optional[int] = Query(50, description="Nombre maximum d'éléments à retourner", ge=1, le=500),
    offset: Optional[int] = Query(0, description="Décalage pour la pagination", ge=0)
):
    """
    Récupère une liste d'éléments GLPI par type.
    
    **Paramètres :**
    - `item_type`: Type d'élément à récupérer
      - Computer: Ordinateurs
      - User: Utilisateurs
      - Ticket: Tickets/Incidents
      - Printer: Imprimantes
      - etc.
    - `limit`: Nombre maximum de résultats (1-500)
    - `offset`: Décalage pour la pagination
    
    **Retourne :**
    - `status`: Statut de la requête ("success" ou "error")
    - `data`: Liste des éléments
    - `count`: Nombre total d'éléments
    
    **Exemple :**
    ```
    GET /glpi/items/Computer?limit=10&offset=0
    ```
    """
    try:
        client = GLPIClient()
        items = client.get_items(item_type, limit, offset)
        return {
            "status": "success",
            "data": items,
            "count": len(items) if isinstance(items, list) else None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Type d'élément non valide: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des éléments: {str(e)}"
        )