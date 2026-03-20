import logging
import httpx
from typing import Any
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


class GLPIClient:
    """
    Wrapper complet de l'API REST GLPI.
    Instancié par requête avec le session_token GLPI de l'utilisateur connecté
    → toutes les actions sont tracées nominativement dans GLPI.
    """

    def __init__(self, session_token: str):
        self._session_token = session_token

    # ------------------------------------------------------------------ #
    #  Méthode de base                                                     #
    # ------------------------------------------------------------------ #

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        response = await self._do_request(method, endpoint, self._session_token, **kwargs)
        logger.debug("GLPI %s %s → %s", method, endpoint, response.status_code)

        # Session expirée → forcer une reconnexion
        is_not_auth = response.status_code in (401, 403) and "Not Authentified" in response.text
        if response.status_code == 401 or is_not_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session GLPI expirée, veuillez vous reconnecter.",
            )

        self._raise_for_glpi_error(response)
        return response.json() if response.content else None

    async def _do_request(self, method: str, endpoint: str, token: str, **kwargs) -> httpx.Response:
        headers = {
            "Session-Token": token,
            "App-Token": settings.GLPI_APP_TOKEN,
        }
        if method.upper() not in ("GET", "DELETE"):
            headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await client.request(
                method,
                f"{settings.GLPI_URL}{endpoint}",
                headers=headers,
                **kwargs,
            )

    def _raise_for_glpi_error(self, response: httpx.Response):
        if response.status_code < 400:
            return
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    # ------------------------------------------------------------------ #
    #  CRUD générique (fonctionne pour TOUTE ressource GLPI)              #
    # ------------------------------------------------------------------ #

    async def get_item(self, itemtype: str, item_id: int, **params) -> dict:
        """GET /apirest.php/{itemtype}/{id}"""
        return await self._request("GET", f"/{itemtype}/{item_id}", params=params)

    async def get_all_items(self, itemtype: str, **params) -> list[dict]:
        """GET /apirest.php/{itemtype} — avec pagination automatique"""
        params.setdefault("range", "0-999")
        return await self._request("GET", f"/{itemtype}", params=params)

    async def create_item(self, itemtype: str, input_data: dict) -> dict:
        """POST /apirest.php/{itemtype}"""
        return await self._request("POST", f"/{itemtype}", json={"input": input_data})

    async def update_item(self, itemtype: str, item_id: int, input_data: dict) -> dict:
        """PUT /apirest.php/{itemtype}/{id}"""
        return await self._request("PUT", f"/{itemtype}/{item_id}", json={"input": input_data})

    async def delete_item(self, itemtype: str, item_id: int, force: bool = False) -> dict:
        """DELETE /apirest.php/{itemtype}/{id}"""
        return await self._request("DELETE", f"/{itemtype}/{item_id}", params={"force_purge": force})

    # ------------------------------------------------------------------ #
    #  Recherche                                                           #
    # ------------------------------------------------------------------ #

    async def search(self, itemtype: str, criteria: list[dict] | None = None, **params) -> dict:
        """
        GET /apirest.php/search/{itemtype}
        criteria ex: [{"field": 1, "searchtype": "contains", "value": "réseau"}]
        """
        query_params = {**params}
        if criteria:
            # GLPI attend criteria[0][field]=..., criteria[0][searchtype]=..., etc.
            for i, crit in enumerate(criteria):
                for k, v in crit.items():
                    query_params[f"criteria[{i}][{k}]"] = v
        return await self._request("GET", f"/search/{itemtype}", params=query_params)

    async def list_search_options(self, itemtype: str) -> dict:
        """GET /apirest.php/listSearchOptions/{itemtype}"""
        return await self._request("GET", f"/listSearchOptions/{itemtype}")

    # ------------------------------------------------------------------ #
    #  Sous-items (followups, solutions, documents liés...)               #
    # ------------------------------------------------------------------ #

    async def get_sub_items(self, itemtype: str, item_id: int, sub_itemtype: str, **params) -> list[dict]:
        """GET /apirest.php/{itemtype}/{id}/{sub_itemtype}"""
        return await self._request("GET", f"/{itemtype}/{item_id}/{sub_itemtype}", params=params)

    async def create_sub_item(self, itemtype: str, item_id: int, sub_itemtype: str, input_data: dict) -> dict:
        """POST /apirest.php/{itemtype}/{id}/{sub_itemtype}"""
        return await self._request("POST", f"/{itemtype}/{item_id}/{sub_itemtype}", json={"input": input_data})

    # ------------------------------------------------------------------ #
    #  Ressources spécifiques : Tickets                                   #
    # ------------------------------------------------------------------ #

    async def get_ticket(self, ticket_id: int) -> dict:
        return await self.get_item("Ticket", ticket_id)

    async def get_tickets(self, **params) -> list[dict]:
        return await self.get_all_items("Ticket", **params)

    async def create_ticket(self, data: dict) -> dict:
        return await self.create_item("Ticket", data)

    async def update_ticket(self, ticket_id: int, data: dict) -> dict:
        return await self.update_item("Ticket", ticket_id, data)

    async def close_ticket(self, ticket_id: int) -> dict:
        """Status 6 = Closed dans GLPI"""
        return await self.update_item("Ticket", ticket_id, {"status": 6})

    async def get_followups(self, ticket_id: int) -> list[dict]:
        return await self.get_sub_items("Ticket", ticket_id, "ITILFollowup")

    async def add_followup(self, ticket_id: int, content: str, is_private: bool = False) -> dict:
        return await self.create_sub_item("Ticket", ticket_id, "ITILFollowup", {
            "content": content,
            "is_private": is_private,
        })

    async def get_solution(self, ticket_id: int) -> list[dict]:
        return await self.get_sub_items("Ticket", ticket_id, "ITILSolution")

    async def add_solution(self, ticket_id: int, content: str, solution_type_id: int = 0) -> dict:
        return await self.create_sub_item("Ticket", ticket_id, "ITILSolution", {
            "content": content,
            "solutiontypes_id": solution_type_id,
        })

    async def get_ticket_documents(self, ticket_id: int) -> list[dict]:
        return await self.get_sub_items("Ticket", ticket_id, "Document_Item")

    # ------------------------------------------------------------------ #
    #  Ressources spécifiques : Base de connaissances                     #
    # ------------------------------------------------------------------ #

    async def get_knowbase_items(self, **params) -> list[dict]:
        return await self.get_all_items("KnowbaseItem", **params)
    
    async def get_knowbase_item(self, item_id: int) -> dict:
        return await self.get_item("KnowbaseItem", item_id)
    
    async def get_knowbase_categories(self) -> list[dict]:
        return await self.get_all_items("KnowbaseItemCategory")
    
    async def get_knowbase_comments(self, item_id: int) -> list[dict]:
        return await self.get_sub_items("KnowbaseItem", item_id, "KnowbaseItem_Comment")
    
    async def add_knowbase_comment(self, item_id: int, content: str, is_private: bool = False) -> dict:
        return await self.create_sub_item("KnowbaseItem", item_id, "KnowbaseItem_Comment", {
            "content": content,
        })
    
    async def search_knowbase(self, query: str) -> dict:
        return await self.search("KnowbaseItem", criteria=[{
            "field": 1,  # Title
            "searchtype": "contains",
            "value": query
        }])

    # ------------------------------------------------------------------ #
    #  Ressources spécifiques : Users & Groups                            #
    # ------------------------------------------------------------------ #

    async def get_user(self, user_id: int) -> dict:
        return await self.get_item("User", user_id)

    async def get_users(self, **params) -> list[dict]:
        return await self.get_all_items("User", **params)

    async def get_current_user_profile(self) -> dict | None:
        """Retourne le profil GLPI de l'utilisateur de la session active."""
        session = await self._request("GET", "/getFullSession")
        user_id = session.get("session", {}).get("glpiID")
        if not user_id:
            return None
        return await self.get_user(user_id)

    async def get_group(self, group_id: int) -> dict:
        return await self.get_item("Group", group_id)

    async def get_groups(self, **params) -> list[dict]:
        return await self.get_all_items("Group", **params)

    async def get_user_groups(self, user_id: int) -> list[dict]:
        return await self.get_sub_items("User", user_id, "Group_User")

    async def get_group_users(self, group_id: int) -> list[dict]:
        return await self.get_sub_items("Group", group_id, "Group_User")

