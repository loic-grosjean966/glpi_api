from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_current_user_admin, get_glpi_client
from app.core.glpi_client import GLPIClient

router = APIRouter(tags=["Users & Groups"])


# ------------------------------------------------------------------ #
#  Users                                                               #
# ------------------------------------------------------------------ #

@router.get("/users")
async def list_users(
    current_user: dict = Depends(get_current_user_admin),  # Admin only
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_users()


@router.get("/users/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    """Retourne l'utilisateur GLPI correspondant au user connecté."""
    return await glpi.get_user_by_name(current_user["sub"])


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_user(user_id)


@router.get("/users/{user_id}/groups")
async def get_user_groups(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_user_groups(user_id)


# ------------------------------------------------------------------ #
#  Groups                                                              #
# ------------------------------------------------------------------ #

@router.get("/groups")
async def list_groups(
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_groups()


@router.get("/groups/{group_id}")
async def get_group(
    group_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_group(group_id)


@router.get("/groups/{group_id}/users")
async def get_group_users(
    group_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_group_users(group_id)
