from asyncio import Lock


class GLPITokenStore:
    """Stocke les session_tokens GLPI côté serveur, indexés par username."""

    def __init__(self):
        self._tokens: dict[str, str] = {}  # username → glpi_session_token
        self._lock = Lock()

    async def set(self, username: str, token: str) -> None:
        async with self._lock:
            self._tokens[username] = token

    def get(self, username: str) -> str | None:
        return self._tokens.get(username)

    async def delete(self, username: str) -> None:
        async with self._lock:
            self._tokens.pop(username, None)


class RefreshTokenStore:
    """
    Stocke les refresh tokens côté serveur (mémoire).
    refresh_token → username. Permet la révocation immédiate au logout.
    """

    def __init__(self):
        self._tokens: dict[str, str] = {}  # refresh_token → username
        self._lock = Lock()

    async def set(self, refresh_token: str, username: str) -> None:
        async with self._lock:
            self._tokens[refresh_token] = username

    def get_username(self, refresh_token: str) -> str | None:
        return self._tokens.get(refresh_token)

    async def delete(self, refresh_token: str) -> None:
        async with self._lock:
            self._tokens.pop(refresh_token, None)

    async def delete_all_for_user(self, username: str) -> None:
        async with self._lock:
            to_remove = [k for k, v in self._tokens.items() if v == username]
            for k in to_remove:
                del self._tokens[k]


glpi_token_store = GLPITokenStore()
refresh_token_store = RefreshTokenStore()
