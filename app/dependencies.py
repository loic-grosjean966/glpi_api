from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_jwt
from app.core.token_store import glpi_token_store
from app.core.glpi_client import GLPIClient

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Vérifie le JWT et retourne le payload (username, groups, etc.)"""
    return decode_jwt(credentials.credentials)


async def get_current_user_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Restreint l'accès aux membres du groupe AD 'DSI' ou 'Administrateurs'."""
    allowed_groups = {"DSI", "Administrateurs"}
    user_groups = set(current_user.get("groups", []))
    if not allowed_groups.intersection(user_groups):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_user


async def get_glpi_client(
    current_user: dict = Depends(get_current_user),
) -> GLPIClient:
    """Instancie un GLPIClient avec le token GLPI de l'utilisateur connecté."""
    user_token = glpi_token_store.get(current_user["sub"])
    if not user_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session expirée, veuillez vous reconnecter",
        )
    return GLPIClient(user_token)
