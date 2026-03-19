from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_current_user_admin, get_glpi_client
from app.core.glpi_client import GLPIClient

router = APIRouter(tags=["Utilisateurs & Groupes"])


# ------------------------------------------------------------------ #
#  Users                                                               #
# ------------------------------------------------------------------ #

@router.get(
    "/users",
    summary="Lister tous les utilisateurs GLPI",
    description="Retourne la liste complète des utilisateurs enregistrés dans GLPI.\n\n> **Accès restreint** — réservé aux membres des groupes AD `DSI` ou `Administrateurs`.",
    responses={
        200: {"description": "Liste des utilisateurs GLPI"},
        401: {"description": "Token manquant ou expiré"},
        403: {"description": "Accès refusé — droits administrateur requis"},
    },
)
async def list_users(
    current_user: dict = Depends(get_current_user_admin),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_users()


@router.get(
    "/users/me",
    summary="Mon profil GLPI",
    description="Retourne le profil GLPI de l'utilisateur actuellement connecté, tel qu'il est enregistré dans GLPI (nom, email, groupes GLPI, etc.).",
    responses={
        200: {"description": "Profil GLPI de l'utilisateur connecté"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Utilisateur introuvable dans GLPI"},
    },
)
async def get_me(
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_user_by_name(current_user["sub"])


@router.get(
    "/users/{user_id}",
    summary="Détail d'un utilisateur",
    description="Retourne le profil GLPI d'un utilisateur par son ID GLPI.",
    responses={
        200: {"description": "Profil de l'utilisateur"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Utilisateur introuvable"},
    },
)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_user(user_id)


@router.get(
    "/users/{user_id}/groups",
    summary="Groupes d'un utilisateur",
    description="Retourne la liste des groupes GLPI auxquels appartient l'utilisateur.",
    responses={
        200: {"description": "Liste des groupes de l'utilisateur"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Utilisateur introuvable"},
    },
)
async def get_user_groups(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_user_groups(user_id)


# ------------------------------------------------------------------ #
#  Groups                                                              #
# ------------------------------------------------------------------ #

@router.get(
    "/groups",
    summary="Lister tous les groupes GLPI",
    description="Retourne la liste de tous les groupes définis dans GLPI.",
    responses={
        200: {"description": "Liste des groupes"},
        401: {"description": "Token manquant ou expiré"},
    },
)
async def list_groups(
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_groups()


@router.get(
    "/groups/{group_id}",
    summary="Détail d'un groupe",
    description="Retourne les informations d'un groupe GLPI par son ID.",
    responses={
        200: {"description": "Détail du groupe"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Groupe introuvable"},
    },
)
async def get_group(
    group_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_group(group_id)


@router.get(
    "/groups/{group_id}/users",
    summary="Membres d'un groupe",
    description="Retourne la liste des utilisateurs GLPI appartenant au groupe.",
    responses={
        200: {"description": "Liste des membres du groupe"},
        401: {"description": "Token manquant ou expiré"},
        404: {"description": "Groupe introuvable"},
    },
)
async def get_group_users(
    group_id: int,
    current_user: dict = Depends(get_current_user),
    glpi: GLPIClient = Depends(get_glpi_client),
):
    return await glpi.get_group_users(group_id)
