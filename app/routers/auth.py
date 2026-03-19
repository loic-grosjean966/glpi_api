import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from app.core.ldap import ldap_authenticate
from app.core.security import create_jwt
from app.core.glpi_session import glpi_session_manager
from app.core.token_store import glpi_token_store
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    display_name: str
    groups: list[str]


async def _get_glpi_user_token(username: str) -> str | None:
    """
    Utilise le compte de service pour récupérer le personal_token
    GLPI de l'utilisateur (nécessaire pour les sessions nominatives).
    """
    try:
        service_session = await glpi_session_manager.get_token(settings.GLPI_USER_TOKEN)
    except Exception:
        return None

    headers = {
        "Session-Token": service_session,
        "App-Token": settings.GLPI_APP_TOKEN,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Recherche de l'utilisateur par son login
        resp = await client.get(
            f"{settings.GLPI_URL}/User",
            headers=headers,
            params={"searchText[name]": username, "range": "0-1"},
        )
        if resp.status_code != 200 or not resp.json():
            return None

        user_id = resp.json()[0]["id"]

        # Récupération du personal_token
        resp2 = await client.get(
            f"{settings.GLPI_URL}/User/{user_id}",
            headers=headers,
        )
        if resp2.status_code != 200:
            return None

        return resp2.json().get("personal_token") or None


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    user_info = await ldap_authenticate(body.username, body.password)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )

    glpi_token = await _get_glpi_user_token(body.username)
    if not glpi_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aucun token API GLPI trouvé pour ce compte. "
                   "Activez l'accès API dans GLPI (Administration > Utilisateurs > Jetons API).",
        )

    await glpi_token_store.set(user_info["username"], glpi_token)

    token = create_jwt({
        "sub": user_info["username"],
        "display_name": user_info["display_name"],
        "email": user_info["email"],
        "groups": user_info["groups"],
        "department": user_info["department"],
    })

    return LoginResponse(
        access_token=token,
        display_name=user_info["display_name"],
        groups=user_info["groups"],
    )
