from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_current_user, get_glpi_client
from app.core.glpi_client import GLPIClient

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ------------------------------------------------------------------ #
#  Schemas                                                             #
# ------------------------------------------------------------------ #

class TicketCreate(BaseModel):
    name: str
    content: str
    urgency: int = 3       # 1=Très bas, 2=Bas, 3=Moyen, 4=Haut, 5=Très haut
    type: int = 1          # 1=Incident, 2=Demande
    itilcategories_id: int = 0

class TicketUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    status: int | None = None
    urgency: int | None = None
    assigned_users_id: int | None = None
    assigned_groups_id: int | None = None

class FollowupCreate(BaseModel):
    content: str
    is_private: bool = False

class SolutionCreate(BaseModel):
    content: str
    solutiontypes_id: int = 0


# ------------------------------------------------------------------ #
#  Endpoints                                                           #
# ------------------------------------------------------------------ #

@router.get("")
async def list_tickets(
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_tickets()


@router.get("/search/query")
async def search_tickets(
    q: str = "",
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    criteria = [{"field": 1, "searchtype": "contains", "value": q}] if q else None
    return await glpi.search("Ticket", criteria=criteria)


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_ticket(ticket_id)


@router.post("")
async def create_ticket(
    body: TicketCreate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.create_ticket(body.model_dump())


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.update_ticket(ticket_id, body.model_dump(exclude_none=True))


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.close_ticket(ticket_id)


# Followups
@router.get("/{ticket_id}/followups")
async def get_followups(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_followups(ticket_id)


@router.post("/{ticket_id}/followups")
async def add_followup(
    ticket_id: int,
    body: FollowupCreate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.add_followup(ticket_id, body.content, body.is_private)


# Solutions
@router.get("/{ticket_id}/solution")
async def get_solution(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_solution(ticket_id)


@router.post("/{ticket_id}/solution")
async def add_solution(
    ticket_id: int,
    body: SolutionCreate,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.add_solution(ticket_id, body.content, body.solutiontypes_id)


# Documents
@router.get("/{ticket_id}/documents")
async def get_ticket_documents(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_ticket_documents(ticket_id)

