from fastapi import APIRouter, Query, Path, HTTPException, Body
from typing import Dict, Any
from enum import Enum
from app.glpi.client import GLPIClient


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


ITEM_TYPE_DESCRIPTION = (
    "Type d'objet GLPI (ex: Computer, User, Ticket, Printer, Monitor, "
    "Software, NetworkEquipment, Phone, Peripheral, etc.)"
)

router = APIRouter(prefix="/glpi")


# --- Session & Connexion ---


@router.get(
    "/test",
    tags=["GLPI"],
    summary="Tester la connexion à GLPI",
    description="Initialise une session GLPI, récupère le profil utilisateur, puis ferme la session. "
    "Permet de vérifier que les tokens et l'URL sont correctement configurés.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Connexion réussie",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "session": {"session_token": "83af7e620c83a50a18d3eac2f6ed05a3ca0bea62"},
                        "profile": {"myprofiles": [{"id": 1, "name": "Super-admin"}]},
                    }
                }
            },
        },
        500: {"description": "Erreur de connexion au serveur GLPI"},
    },
)
def test_glpi_connection():
    """
    Test la connexion au serveur GLPI.

    - Initialise une session via `initSession`
    - Récupère les profils utilisateur via `getMyProfiles`
    - Ferme la session via `killSession`
    """
    client = GLPIClient()
    try:
        session = client.init_session()
        profile = client.get_my_profiles()
        return {
            "status": "success",
            "session": session,
            "profile": profile,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion GLPI: {str(e)}",
        )
    finally:
        client.kill_session()


# --- Profils & Entités ---


@router.get(
    "/profiles",
    tags=["User"],
    summary="Récupérer les profils utilisateur",
    description="Retourne tous les profils associés à l'utilisateur connecté. "
    "Correspond à l'endpoint GLPI `getMyProfiles`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Liste des profils",
            "content": {
                "application/json": {
                    "example": {
                        "myprofiles": [
                            {"id": 1, "name": "Super-admin"},
                            {"id": 2, "name": "Technician"},
                        ]
                    }
                }
            },
        },
        500: {"description": "Erreur serveur"},
    },
)
def get_my_profiles():
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_my_profiles()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


@router.get(
    "/profiles/active",
    tags=["User"],
    summary="Récupérer le profil actif",
    description="Retourne le profil actuellement actif pour la session. "
    "Correspond à l'endpoint GLPI `getActiveProfile`.",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Profil actif"},
        500: {"description": "Erreur serveur"},
    },
)
def get_active_profile():
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_active_profile()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


@router.get(
    "/entities",
    tags=["User"],
    summary="Récupérer les entités accessibles",
    description="Retourne toutes les entités accessibles par l'utilisateur connecté "
    "(pour le profil actif). Correspond à l'endpoint GLPI `getMyEntities`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Liste des entités",
            "content": {
                "application/json": {
                    "example": {
                        "myentities": [
                            {"id": 0, "name": "Root Entity"},
                            {"id": 71, "name": "my_entity"},
                        ]
                    }
                }
            },
        },
        500: {"description": "Erreur serveur"},
    },
)
def get_my_entities(
    is_recursive: bool = Query(
        False, description="Afficher aussi les sous-entités de l'entité active"
    ),
):
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_my_entities(is_recursive)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


@router.get(
    "/entities/active",
    tags=["User"],
    summary="Récupérer les entités actives",
    description="Retourne les entités actives de l'utilisateur connecté. "
    "Correspond à l'endpoint GLPI `getActiveEntities`.",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Entités actives"},
        500: {"description": "Erreur serveur"},
    },
)
def get_active_entities():
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_active_entities()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


# --- Session & Configuration ---


@router.get(
    "/session",
    tags=["GLPI"],
    summary="Récupérer la session complète",
    description="Retourne les informations complètes de la session PHP active. "
    "Correspond à l'endpoint GLPI `getFullSession`.",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Données de session complètes"},
        500: {"description": "Erreur serveur"},
    },
)
def get_full_session():
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_full_session()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


@router.get(
    "/config",
    tags=["GLPI"],
    summary="Récupérer la configuration GLPI",
    description="Retourne la configuration globale de GLPI (`$CFG_GLPI`). "
    "Correspond à l'endpoint GLPI `getGlpiConfig`.",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Configuration GLPI"},
        500: {"description": "Erreur serveur"},
    },
)
def get_glpi_config():
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_glpi_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


# --- CRUD Items ---


@router.get(
    "/items/{item_type}",
    tags=["Item"],
    summary="Récupérer tous les éléments d'un type",
    description="Retourne une collection d'éléments du type spécifié. "
    "Supporte la pagination via `limit`/`offset` et le tri via `sort`/`order`. "
    "Correspond à l'endpoint GLPI `GET /:itemtype/`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Liste d'éléments récupérée avec succès",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": [
                            {"id": 1, "name": "PC-001", "serial": "ABC123"},
                            {"id": 2, "name": "PC-002", "serial": "DEF456"},
                        ],
                        "count": 2,
                    }
                }
            },
        },
        500: {"description": "Erreur serveur lors de la récupération"},
    },
)
def get_items(
    item_type: str = Path(..., description=ITEM_TYPE_DESCRIPTION),
    limit: int = Query(50, description="Nombre maximum d'éléments à retourner", ge=1, le=500),
    offset: int = Query(0, description="Décalage pour la pagination", ge=0),
    sort: int = Query(1, description="ID du champ de tri (searchOption). 1=nom, 2=id, etc."),
    order: SortOrder = Query(SortOrder.ASC, description="Ordre de tri"),
    expand_dropdowns: bool = Query(
        False, description="Afficher le nom des dropdowns au lieu de leur ID"
    ),
    only_id: bool = Query(False, description="Ne retourner que les IDs"),
):
    """
    **Exemples de types d'éléments :**
    - `Computer` : Ordinateurs
    - `User` : Utilisateurs
    - `Ticket` : Tickets / Incidents
    - `Printer` : Imprimantes
    - `Monitor` : Moniteurs
    - `Software` : Logiciels
    - `NetworkEquipment` : Équipements réseau
    """
    client = GLPIClient()
    try:
        client.init_session()
        items = client.get_items(
            item_type, limit, offset, sort, order.value, expand_dropdowns, only_id
        )
        return {
            "status": "success",
            "data": items,
            "count": len(items) if isinstance(items, list) else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()


@router.get(
    "/items/{item_type}/{item_id}",
    tags=["Item"],
    summary="Récupérer un élément par ID",
    description="Retourne les champs d'un élément identifié par son type et son ID. "
    "Correspond à l'endpoint GLPI `GET /:itemtype/:id`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Élément trouvé",
            "content": {
                "application/json": {
                    "example": {
                        "id": 71,
                        "name": "PC-001",
                        "serial": "12345",
                        "entities_id": 0,
                        "states_id": 1,
                    }
                }
            },
        },
        404: {"description": "Élément non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def get_item(
    item_type: str = Path(..., description=ITEM_TYPE_DESCRIPTION),
    item_id: int = Path(..., description="ID unique de l'élément", ge=1),
    expand_dropdowns: bool = Query(
        False, description="Afficher le nom des dropdowns au lieu de leur ID"
    ),
    with_logs: bool = Query(False, description="Inclure l'historique des modifications"),
):
    client = GLPIClient()
    try:
        client.init_session()
        return client.get_item(item_type, item_id, expand_dropdowns, with_logs)
    except Exception as e:
        status = 404 if "404" in str(e) else 500
        raise HTTPException(status_code=status, detail=str(e))
    finally:
        client.kill_session()


@router.get(
    "/items/{item_type}/{item_id}/{sub_item_type}",
    tags=["Item"],
    summary="Récupérer les sous-éléments",
    description="Retourne les sous-éléments associés à un élément parent. "
    "Par exemple, les logs d'un utilisateur (`User/2/Log`) ou les tickets d'un ordinateur. "
    "Correspond à l'endpoint GLPI `GET /:itemtype/:id/:sub_itemtype`.",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Sous-éléments récupérés avec succès"},
        404: {"description": "Élément parent non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def get_sub_items(
    item_type: str = Path(..., description=ITEM_TYPE_DESCRIPTION),
    item_id: int = Path(..., description="ID unique de l'élément parent", ge=1),
    sub_item_type: str = Path(
        ...,
        description="Type de sous-élément (ex: Log, Ticket, Document, Contract, NetworkPort, etc.)",
    ),
    limit: int = Query(50, description="Nombre maximum d'éléments", ge=1, le=500),
    offset: int = Query(0, description="Décalage pour la pagination", ge=0),
):
    client = GLPIClient()
    try:
        client.init_session()
        data = client.get_sub_items(item_type, item_id, sub_item_type, limit, offset)
        return {
            "status": "success",
            "data": data,
            "count": len(data) if isinstance(data, list) else None,
        }
    except Exception as e:
        status = 404 if "404" in str(e) else 500
        raise HTTPException(status_code=status, detail=str(e))
    finally:
        client.kill_session()


@router.post(
    "/items/{item_type}",
    tags=["Item"],
    summary="Créer un élément",
    description="Crée un ou plusieurs éléments dans GLPI. "
    "Le payload doit contenir les champs de l'objet à créer. "
    "Correspond à l'endpoint GLPI `POST /:itemtype/`.",
    response_model=Dict[str, Any],
    responses={
        201: {
            "description": "Élément créé avec succès",
            "content": {
                "application/json": {
                    "example": {"id": 15, "message": ""}
                }
            },
        },
        400: {"description": "Erreur dans les données fournies"},
        500: {"description": "Erreur serveur"},
    },
    status_code=201,
)
def create_item(
    item_type: str = Path(..., description=ITEM_TYPE_DESCRIPTION),
    data: Dict[str, Any] = Body(
        ...,
        description="Champs de l'élément à créer",
        examples=[{"name": "PC-NEW", "serial": "12345", "entities_id": 0}],
    ),
):
    client = GLPIClient()
    try:
        client.init_session()
        return client.create_item(item_type, data)
    except Exception as e:
        status = 400 if "400" in str(e) else 500
        raise HTTPException(status_code=status, detail=str(e))
    finally:
        client.kill_session()


@router.put(
    "/items/{item_type}/{item_id}",
    tags=["Item"],
    summary="Mettre à jour un élément",
    description="Met à jour les champs d'un élément existant dans GLPI. "
    "Seuls les champs fournis dans le payload seront modifiés. "
    "Correspond à l'endpoint GLPI `PUT /:itemtype/:id`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Élément mis à jour",
            "content": {
                "application/json": {
                    "example": [{"10": True, "message": ""}]
                }
            },
        },
        404: {"description": "Élément non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def update_item(
    item_type: str = Path(..., description=ITEM_TYPE_DESCRIPTION),
    item_id: int = Path(..., description="ID unique de l'élément à modifier", ge=1),
    data: Dict[str, Any] = Body(
        ...,
        description="Champs à mettre à jour",
        examples=[{"name": "PC-UPDATED", "serial": "67890"}],
    ),
):
    client = GLPIClient()
    try:
        client.init_session()
        return client.update_item(item_type, item_id, data)
    except Exception as e:
        status = 404 if "404" in str(e) else 500
        raise HTTPException(status_code=status, detail=str(e))
    finally:
        client.kill_session()


@router.delete(
    "/items/{item_type}/{item_id}",
    tags=["Item"],
    summary="Supprimer un élément",
    description="Supprime un élément de GLPI. Par défaut, l'élément est mis dans la corbeille. "
    "Utilisez `force_purge=true` pour une suppression définitive. "
    "Correspond à l'endpoint GLPI `DELETE /:itemtype/:id`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Élément supprimé",
            "content": {
                "application/json": {
                    "example": [{"16": True, "message": ""}]
                }
            },
        },
        404: {"description": "Élément non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_item(
    item_type: str = Path(..., description=ITEM_TYPE_DESCRIPTION),
    item_id: int = Path(..., description="ID unique de l'élément à supprimer", ge=1),
    force_purge: bool = Query(
        False,
        description="Supprimer définitivement (ignorer la corbeille)",
    ),
):
    client = GLPIClient()
    try:
        client.init_session()
        return client.delete_item(item_type, item_id, force_purge)
    except Exception as e:
        status = 404 if "404" in str(e) else 500
        raise HTTPException(status_code=status, detail=str(e))
    finally:
        client.kill_session()


# --- Recherche ---


@router.get(
    "/search/{item_type}",
    tags=["Item"],
    summary="Rechercher des éléments",
    description="Utilise le moteur de recherche GLPI pour rechercher des éléments avec des critères avancés. "
    "Supporte les opérateurs : `contains`, `equals`, `notequals`, `lessthan`, `morethan`, `under`, `notunder`. "
    "Vous pouvez utiliser le type `AllAssets` pour rechercher dans tous les types d'assets. "
    "Correspond à l'endpoint GLPI `GET /search/:itemtype/`.",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Résultats de recherche",
            "content": {
                "application/json": {
                    "example": {
                        "totalcount": 35,
                        "count": 10,
                        "data": [
                            {"1": "PC-001", "2": 71, "80": "Root Entity"},
                        ],
                    }
                }
            },
        },
        500: {"description": "Erreur serveur"},
    },
)
def search_items(
    item_type: str = Path(
        ...,
        description=ITEM_TYPE_DESCRIPTION + ". Utilisez 'AllAssets' pour tous les types.",
    ),
    limit: int = Query(50, description="Nombre maximum de résultats", ge=1, le=500),
    offset: int = Query(0, description="Décalage pour la pagination", ge=0),
    sort: int = Query(1, description="ID du searchOption pour le tri"),
    order: SortOrder = Query(SortOrder.ASC, description="Ordre de tri"),
):
    """
    **Note :** Pour des critères de recherche avancés (filtres multiples, meta-critères),
    utilisez directement l'API GLPI. Cet endpoint expose une recherche simplifiée.

    **searchOptions courants :**
    - `1` : Nom
    - `2` : ID
    - `3` : Lieu
    - `31` : Statut
    - `80` : Entité
    """
    client = GLPIClient()
    try:
        client.init_session()
        return client.search_items(item_type, limit=limit, offset=offset, sort=sort, order=order.value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.kill_session()
