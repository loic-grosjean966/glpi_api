import base64
import logging
import secrets
import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from app.core.ldap import ldap_authenticate
from app.core.security import create_jwt
from app.core.token_store import glpi_token_store, refresh_token_store
from app.core.config import settings
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentification"])


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        description="Identifiant Active Directory (sans le domaine). Ex : `jean.dupont`",
        examples=["jean.dupont"],
    )
    password: str = Field(
        ...,
        description="Mot de passe du compte Active Directory",
    )


class LoginResponse(BaseModel):
    access_token: str = Field(description="JWT Bearer token (30 min) — à inclure dans le header `Authorization`.")
    refresh_token: str = Field(description="Token opaque (30 jours) — à utiliser sur `POST /auth/refresh` pour renouveler l'access token.")
    token_type: str = Field(default="bearer", description="Type de token — toujours `bearer`")
    display_name: str = Field(description="Nom complet de l'utilisateur (depuis l'AD)")
    groups: list[str] = Field(description="Groupes Active Directory de l'utilisateur")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token obtenu lors du login")


class RefreshResponse(BaseModel):
    access_token: str = Field(description="Nouvel access token JWT (30 min)")
    token_type: str = Field(default="bearer")


async def _init_glpi_session(username: str, password: str) -> str | None:
    """
    Ouvre une session GLPI nominative via Basic Auth (username:password).
    Retourne le session_token GLPI ou None si échec.
    """
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{settings.GLPI_URL}/initSession",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "App-Token": settings.GLPI_APP_TOKEN,
                },
            )
            if resp.status_code != 200:
                logger.error(f"[init_glpi_session] Échec pour '{username}' : {resp.status_code} {resp.text}")
                return None
            return resp.json().get("session_token")
        except Exception as e:
            logger.error(f"[init_glpi_session] Erreur : {e}")
            return None


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Connexion",
    description="""
Authentifie un utilisateur via **Active Directory** (LDAP) et ouvre une session GLPI nominative.

Retourne deux tokens :
- **`access_token`** (JWT, 30 min) — à inclure dans le header `Authorization: Bearer <token>`
- **`refresh_token`** (opaque, 30 jours) — à utiliser sur `POST /auth/refresh` pour renouveler silencieusement l'access token

> **Limite :** 5 tentatives par minute par adresse IP. Au-delà : `429 Too Many Requests`.
""",
    responses={
        200: {"description": "Connexion réussie — retourne le JWT et les infos utilisateur"},
        401: {"description": "Identifiants AD invalides"},
        403: {"description": "Compte GLPI sans token API actif — activer dans GLPI : Administration > Utilisateurs > Jetons API"},
        429: {"description": "Trop de tentatives — réessayer dans 1 minute"},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    user_info = await ldap_authenticate(body.username, body.password)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )

    glpi_session = await _init_glpi_session(body.username, body.password)
    if not glpi_session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible d'ouvrir une session GLPI. "
                   "Vérifiez que le compte existe dans GLPI et que l'App-Token est valide.",
        )

    await glpi_token_store.set(user_info["username"], glpi_session)

    jwt_payload = {
        "sub": user_info["username"],
        "display_name": user_info["display_name"],
        "email": user_info["email"],
        "groups": user_info["groups"],
        "department": user_info["department"],
    }
    access_token = create_jwt(jwt_payload)
    refresh_token = secrets.token_urlsafe(32)
    await refresh_token_store.set(refresh_token, user_info["username"])

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        display_name=user_info["display_name"],
        groups=user_info["groups"],
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Renouveler l'access token",
    description="""
Échange un **refresh token** valide contre un nouvel **access token** JWT (30 min).

À appeler silencieusement depuis l'application mobile quand l'access token expire,
sans redemander les identifiants à l'utilisateur.

> Le refresh token reste valide 30 jours. Il est invalidé au logout.
""",
    responses={
        200: {"description": "Nouvel access token émis"},
        401: {"description": "Refresh token invalide ou expiré — reconnexion requise"},
    },
)
async def refresh(body: RefreshRequest):
    username = refresh_token_store.get_username(body.refresh_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré, veuillez vous reconnecter.",
        )
    access_token = create_jwt({"sub": username})
    return RefreshResponse(access_token=access_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Déconnexion",
    description="Invalide le refresh token. L'access token reste valide jusqu'à son expiration naturelle (30 min max).",
    responses={
        204: {"description": "Déconnexion réussie"},
    },
)
async def logout(body: RefreshRequest):
    await refresh_token_store.delete(body.refresh_token)
