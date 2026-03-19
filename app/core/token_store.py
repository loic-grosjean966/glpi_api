from asyncio import Lock


class GLPITokenStore:
    """
    Stocke les personal_tokens GLPI côté serveur (mémoire),
    indexés par username. Évite de les exposer dans le payload JWT.
    """

    def __init__(self):
        self._tokens: dict[str, str] = {}  # username → glpi_user_token
        self._lock = Lock()

    async def set(self, username: str, token: str) -> None:
        async with self._lock:
            self._tokens[username] = token

    def get(self, username: str) -> str | None:
        return self._tokens.get(username)

    async def delete(self, username: str) -> None:
        async with self._lock:
            self._tokens.pop(username, None)


glpi_token_store = GLPITokenStore()
