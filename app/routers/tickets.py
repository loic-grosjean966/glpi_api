from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from app.dependencies import get_current_user, get_glpi_client
from app.core.glpi_client import GLPIClient

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ------------------------------------------------------------------ #
#  Schemas                                                             #
# ------------------------------------------------------------------ #

class TicketCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(..., description="Titre du ticket", examples=["Imprimante bureau 12 hors service"])
    content: str = Field(..., description="Description détaillée du problème ou de la demande", examples=["L'imprimante HP LaserJet du bureau 12 ne répond plus depuis ce matin."])
    urgency: int = Field(
        default=3,
        ge=1, le=5,
        description="Niveau d'urgence : `1` = Très haute, `2` = Haute, `3` = Moyenne, `4` = Basse, `5` = Très basse",
        examples=[3],
    )
    type: int = Field(
        default=1,
        description="Type de ticket : `1` = Incident, `2` = Demande",
        examples=[1],
    )
    itilcategories_id: int = Field(
        default=0,
        description="ID de la catégorie ITIL dans GLPI. `0` = aucune catégorie",
        examples=[0],
    )
    _users_id_requester: int | None = Field(
        default=None,
        description="ID GLPI du demandeur. Par défaut, le ticket est créé au nom de l'utilisateur connecté (ID extrait de son token GLPI).",
        examples=[123],
    )
    _groups_id_requester: int | None = Field(
        default=None,
        description="ID GLPI du groupe demandeur. Optionnel, rarement utilisé.",
        examples=[45],
    )
    _users_id_assign: int | None = Field(
        default=None,
        description="ID GLPI du technicien à affecter dès la création. Par défaut, le ticket est créé sans affectation (statut 'Nouveau').",
        examples=[67],
    )
    _groups_id_assign: int | None = Field(
        default=None,
        description="ID GLPI du groupe à affecter dès la création. Par défaut, le ticket est créé sans affectation (statut 'Nouveau').",
        examples=[89],
    )
    _users_id_observer: list[int] | None = Field(
        default=None,
        description="Liste d'IDs GLPI des utilisateurs à ajouter en observateurs du ticket. Optionnel.",
        examples=[[123, 456]],
    )  
    _groups_id_observer: list[int] | None = Field(
        default=None,
        description="Liste d'IDs GLPI des groupes à ajouter en observateurs du ticket. Optionnel.",
        examples=[[45, 67]],
    )


class TicketUpdate(BaseModel):
    name: str | None = Field(default=None, description="Nouveau titre du ticket")
    content: str | None = Field(default=None, description="Nouveau contenu / description")
    status: int | None = Field(
        default=None,
        description="Statut : `1` = Nouveau, `2` = En cours (attribué), `3` = En cours (planifié), `4` = En attente, `5` = Résolu, `6` = Clos",
    )
    urgency: int | None = Field(default=None, ge=1, le=5, description="Niveau d'urgence (1 à 5)")
    assigned_users_id: int | None = Field(default=None, description="ID GLPI du technicien à affecter")
    assigned_groups_id: int | None = Field(default=None, description="ID GLPI du groupe à affecter")


class FollowupCreate(BaseModel):
    content: str = Field(..., description="Texte du suivi", examples=["Technicien en déplacement, intervention prévue demain matin."])
    is_private: bool = Field(default=False, description="Si `true`, le suivi est visible uniquement par les techniciens (non visible par le demandeur)")


class SolutionCreate(BaseModel):
    content: str = Field(..., description="Description de la solution apportée", examples=["Remplacement du câble réseau défectueux."])
    solutiontypes_id: int = Field(default=0, description="ID du type de solution dans GLPI. `0` = aucun type")


# ------------------------------------------------------------------ #
#  Endpoints                                                           #
# ------------------------------------------------------------------ #

@router.get(
    "",
    summary="Lister les tickets",
    description="Retourne tous les tickets accessibles par l'utilisateur connecté (jusqu'à 1000 résultats).",
    responses={
        200: {"description": "Liste des tickets"},
        401: {"description": "Token manquant ou expiré"},
        403: {"description": "Session expirée — se reconnecter"},
    },
)
async def list_tickets(
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_tickets()


@router.get(
    "/search/query",
    summary="Rechercher des tickets",
    description="Recherche des tickets dont le **titre contient** la chaîne `q`. Sans paramètre, retourne tous les tickets (même comportement que `GET /tickets`).",
    responses={
        200: {"description": "Résultats de la recherche"},
        401: {"description": "Token manquant ou expiré"},
    },
)
async def search_tickets(
    q: str = Query(default="", description="Texte à rechercher dans le titre des tickets", examples=["imprimante"]),
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    criteria = [{"field": 1, "searchtype": "contains", "value": q}] if q else None
    return await glpi.search("Ticket", criteria=criteria)


@router.get(
    "/{ticket_id}",
    summary="Détail d'un ticket",
    description="Retourne toutes les informations d'un ticket GLPI par son ID.",
    responses={
        200: {"description": "Détail du ticket"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def get_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_ticket(ticket_id)


@router.post(
    "",
    summary="Créer un ticket",
    description="""
Crée un nouveau ticket dans GLPI. Le ticket est créé **au nom de l'utilisateur connecté**
(traçabilité nominative via son token GLPI personnel).

**Valeurs d'urgence :** `1` Très haute · `2` Haute · `3` Moyenne *(défaut)* · `4` Basse · `5` Très basse

**Types :** `1` Incident *(défaut)* · `2` Demande
""",
    status_code=201,
    responses={
        201: {"description": "Ticket créé — retourne l'ID et les infos du ticket"},
        401: {"description": "Token manquant ou expiré"},
        422: {"description": "Données invalides (champs manquants ou valeurs hors plage)"},
    },
)
async def create_ticket(
    body: TicketCreate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.create_ticket(body.model_dump())


@router.put(
    "/{ticket_id}",
    summary="Modifier un ticket",
    description="Met à jour un ou plusieurs champs d'un ticket existant. Seuls les champs fournis sont modifiés (les champs `null` sont ignorés).",
    responses={
        200: {"description": "Ticket mis à jour"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
        422: {"description": "Données invalides"},
    },
)
async def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.update_ticket(ticket_id, body.model_dump(exclude_none=True))


@router.post(
    "/{ticket_id}/close",
    summary="Clôturer un ticket",
    description="Passe le statut du ticket à **Clos** (statut `6` dans GLPI). Cette action est définitive — un ticket clos ne peut pas être réouvert via cette API.",
    responses={
        200: {"description": "Ticket clos"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def close_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.close_ticket(ticket_id)


@router.get(
    "/{ticket_id}/followups",
    summary="Suivis d'un ticket",
    description="Retourne la liste de tous les suivis (notes internes et publiques) associés au ticket.",
    responses={
        200: {"description": "Liste des suivis"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def get_followups(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_followups(ticket_id)


@router.post(
    "/{ticket_id}/followups",
    summary="Ajouter un suivi",
    description="Ajoute un suivi (note) au ticket. Le suivi peut être **public** (visible par le demandeur) ou **privé** (techniciens uniquement).",
    responses={
        200: {"description": "Suivi ajouté"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def add_followup(
    ticket_id: int,
    body: FollowupCreate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.add_followup(ticket_id, body.content, body.is_private)


@router.get(
    "/{ticket_id}/solution",
    summary="Solution d'un ticket",
    description="Retourne la ou les solutions enregistrées sur le ticket.",
    responses={
        200: {"description": "Solution(s) du ticket"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def get_solution(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_solution(ticket_id)


@router.post(
    "/{ticket_id}/solution",
    summary="Ajouter une solution",
    description="Enregistre une solution sur le ticket. Le ticket passe automatiquement au statut **Résolu** dans GLPI.",
    responses={
        200: {"description": "Solution enregistrée, ticket passé en Résolu"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def add_solution(
    ticket_id: int,
    body: SolutionCreate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.add_solution(ticket_id, body.content, body.solutiontypes_id)


@router.get(
    "/{ticket_id}/documents",
    summary="Documents d'un ticket",
    description="Retourne la liste des documents (pièces jointes) associés au ticket.",
    responses={
        200: {"description": "Liste des documents"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Ticket introuvable"},
    },
)
async def get_ticket_documents(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_ticket_documents(ticket_id)
