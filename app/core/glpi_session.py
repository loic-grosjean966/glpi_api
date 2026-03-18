import httpx
from asyncio import Lock
from app.core.config import settings


class GLPISessionManager:
    """
    Gère les sessions GLPI par user_token.
    Chaque utilisateur a sa propre session GLPI → traçabilité nominative.
    Thread-safe grâce à asyncio.Lock.
    """

    def __init__(self):
        self._sessions: dict[str, str] = {}  # user_token → session_token
        self._lock = Lock()

    async def get_token(self, user_token: str) -> str:
        async with self._lock:
            if user_token not in self._sessions:
                await self._init_session(user_token)
            return self._sessions[user_token]

    async def invalidate(self, user_token: str):
        """Appelé quand GLPI retourne 401/403 — force la réinitialisation."""
        async with self._lock:
            self._sessions.pop(user_token, None)

    async def _init_session(self, user_token: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.GLPI_URL}/initSession",
                headers={
                    "Authorization": f"user_token {user_token}",
                    "App-Token": settings.GLPI_APP_TOKEN,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            self._sessions[user_token] = resp.json()["session_token"]

    async def kill_session(self, user_token: str):
        session_token = self._sessions.pop(user_token, None)
        if not session_token:
            return
        async with httpx.AsyncClient() as client:
            await client.get(
                f"{settings.GLPI_URL}/killSession",
                headers={
                    "Session-Token": session_token,
                    "App-Token": settings.GLPI_APP_TOKEN,
                },
            )


glpi_session_manager = GLPISessionManager()
