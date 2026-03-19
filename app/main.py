import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.core.glpi_session import glpi_session_manager
from app.core.config import settings
from app.routers import auth, tickets, users

# Branche les loggers de l'app sur le handler uvicorn
for _name in ("app.core.glpi_client", "app.core.glpi_session", "app.core.ldap"):
    _log = logging.getLogger(_name)
    _log.setLevel(logging.DEBUG)
    _log.propagate = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup : vérifie que le compte de service GLPI est joignable
    await glpi_session_manager.get_token(settings.GLPI_USER_TOKEN)
    yield
    # Shutdown : ferme la session du compte de service
    await glpi_session_manager.kill_session(settings.GLPI_USER_TOKEN)


app = FastAPI(
    title="GLPI API",
    description="Wrapper FastAPI de l'API REST GLPI pour lecreusot.priv",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
