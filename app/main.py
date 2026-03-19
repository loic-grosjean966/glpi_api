import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.core.logging_config import setup_logging
from app.core.glpi_session import glpi_session_manager
from app.core.config import settings
from app.routers import auth, tickets, users

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup : vérifie que le compte de service GLPI est joignable
    await glpi_session_manager.get_token(settings.GLPI_USER_TOKEN)
    yield
    # Shutdown : ferme la session du compte de service
    await glpi_session_manager.kill_session(settings.GLPI_USER_TOKEN)


app = FastAPI(
    title="GLPI API",
    description="""
Wrapper FastAPI de l'API REST GLPI.

## Authentification

Tous les endpoints (sauf `/auth/login` et `/health`) nécessitent un **Bearer token** JWT :

```
Authorization: Bearer <access_token>
```

Obtenir un token : `POST /auth/login` avec vos identifiants Active Directory.
Le token est valide **8 heures**.

## Traçabilité

Chaque action (création, modification, clôture de ticket...) est réalisée avec le token GLPI
**nominatif** de l'utilisateur connecté — toutes les opérations sont tracées dans GLPI
sous son nom.

## Droits administrateur

Certains endpoints sont restreints aux membres des groupes AD `DSI` ou `Administrateurs`.
Ils sont indiqués dans la documentation de chaque route.
""",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentification",
            "description": "Connexion via Active Directory et obtention du JWT.",
        },
        {
            "name": "Tickets",
            "description": "Création, consultation et gestion des tickets GLPI (suivis, solutions, documents).",
        },
        {
            "name": "Utilisateurs & Groupes",
            "description": "Consultation des utilisateurs et groupes GLPI. Certains endpoints sont réservés aux administrateurs.",
        },
    ],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(users.router)


@app.get(
    "/health",
    summary="État de l'API",
    description="Vérifie que l'API est opérationnelle. Ne nécessite pas d'authentification.",
    tags=["Santé"],
)
async def health():
    return {"status": "ok"}
