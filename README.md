# GLPI API Wrapper

Wrapper FastAPI de l'API REST GLPI, avec authentification Active Directory (LDAP) et sessions nominatives par utilisateur.

Développé pour une DSI utilisant Active Directory et GLPI.

---

## Architecture

```
app/
├── main.py              # Point d'entrée FastAPI + health check
├── dependencies.py      # Injection de dépendances (auth, client GLPI)
├── core/
│   ├── config.py        # Configuration via variables d'environnement
│   ├── security.py      # Création / vérification JWT
│   ├── glpi_client.py   # Client HTTP GLPI (wrapper complet)
│   ├── glpi_session.py  # Gestion des sessions GLPI par utilisateur
│   ├── token_store.py   # Stockage serveur des tokens GLPI (hors JWT)
│   ├── limiter.py       # Rate limiter (slowapi)
│   └── ldap.py          # Authentification LDAP / Active Directory
└── routers/
    ├── auth.py          # Endpoints d'authentification
    ├── tickets.py       # Gestion des tickets
    └── users.py         # Utilisateurs et groupes
```

### Flux d'authentification

1. L'utilisateur s'authentifie avec ses identifiants AD (`username@domaine.local`)
2. Après succès LDAP, l'API récupère son `personal_token` GLPI via un compte de service
3. Le `personal_token` GLPI est stocké **côté serveur** (`token_store.py`) — il n'est pas inclus dans le JWT
4. Un JWT (8h) est émis — il contient uniquement les infos de l'utilisateur (nom, groupes, département)
5. Chaque appel API instancie un `GLPIClient` avec le token récupéré depuis le store serveur → traçabilité dans GLPI

> Le compte de service GLPI (`GLPI_USER_TOKEN`) est utilisé uniquement au démarrage (health check) et au login (récupération du token utilisateur).

---

## Endpoints

### Authentification

| Méthode | Chemin | Description | Auth |
|---------|--------|-------------|------|
| POST | `/auth/login` | Connexion (LDAP + GLPI) — limité à **5 tentatives/minute par IP** | Non |

**Body :**
```json
{ "username": "prenom.nom", "password": "motdepasse" }
```

**Réponse :**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "display_name": "Prénom Nom",
  "groups": ["DSI", "..."]
}
```

---

### Tickets

| Méthode | Chemin | Description | Admin |
|---------|--------|-------------|-------|
| GET | `/tickets` | Liste tous les tickets | Non |
| GET | `/tickets/{id}` | Détail d'un ticket | Non |
| GET | `/tickets/search/query` | Recherche par critères | Non |
| POST | `/tickets` | Créer un ticket | Non |
| PUT | `/tickets/{id}` | Modifier un ticket | Non |
| POST | `/tickets/{id}/close` | Clôturer un ticket | Non |
| GET | `/tickets/{id}/followups` | Suivis du ticket | Non |
| POST | `/tickets/{id}/followups` | Ajouter un suivi | Non |
| GET | `/tickets/{id}/solution` | Solution du ticket | Non |
| POST | `/tickets/{id}/solution` | Ajouter une solution | Non |
| GET | `/tickets/{id}/documents` | Documents du ticket | Non |

**Schéma de création :**
```json
{
  "name": "Titre du ticket",
  "content": "Description",
  "urgency": 3,
  "type": 1,
  "itilcategories_id": 0
}
```
> `type` : 1 = Incident, 2 = Demande — `urgency` : 1 (très haute) à 5 (très basse)

---

### Utilisateurs & Groupes

| Méthode | Chemin | Description | Admin |
|---------|--------|-------------|-------|
| GET | `/users` | Liste tous les utilisateurs GLPI | Oui |
| GET | `/users/me` | Profil GLPI de l'utilisateur connecté | Non |
| GET | `/users/{id}` | Détail d'un utilisateur | Non |
| GET | `/users/{id}/groups` | Groupes d'un utilisateur | Non |
| GET | `/groups` | Liste tous les groupes | Non |
| GET | `/groups/{id}` | Détail d'un groupe | Non |
| GET | `/groups/{id}/users` | Membres d'un groupe | Non |

> Les endpoints **Admin** sont restreints aux membres des groupes `DSI` ou `Administrateurs`.

---

### Health Check

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/health` | État de l'API |

---

## Installation

### Prérequis

- Python 3.11+
- Accès à l'instance GLPI avec token applicatif et compte de service
- Accès au contrôleur de domaine AD

### 1. Cloner et installer les dépendances

```bash
git clone <repo>
cd GLPI
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec les vraies valeurs
```

| Variable | Description | Exemple |
|----------|-------------|---------|
| `GLPI_URL` | URL de l'API REST GLPI | `http://glpi.domaine.local/apirest.php` |
| `GLPI_USER_TOKEN` | Token du compte de service GLPI | |
| `GLPI_APP_TOKEN` | Token applicatif GLPI | |
| `LDAP_HOST` | IP ou FQDN du contrôleur de domaine | `192.168.1.10` |
| `LDAP_DOMAIN` | Nom de domaine AD (pour le UPN) | `domaine.local` |
| `LDAP_PORT` | Port LDAP | `389` |
| `LDAP_BASE_DN` | Base DN de recherche | `dc=domaine,dc=local` |
| `LDAP_BIND_USER` | DN du compte de service LDAP | `CN=svc-api,OU=Services,DC=domaine,DC=local` |
| `LDAP_BIND_PASSWORD` | Mot de passe du compte de service LDAP | |
| `JWT_SECRET_KEY` | Clé secrète JWT **(changer en production)** | |
| `JWT_ALGORITHM` | Algorithme JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Durée de validité du token (minutes) | `480` |

### 3. Lancer l'API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Avec Docker

```bash
docker build -t glpi-api .
docker run -p 8000:8000 --env-file .env glpi-api
```

---

## Prérequis GLPI par utilisateur

Chaque technicien doit avoir :
- Un compte GLPI actif
- Le **token personnel** activé : `Administration > Utilisateurs > Paramètres > Jetons API`

Sans ce token, la connexion retourne une erreur `403`.

---

## Utilisation

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "prenom.nom", "password": "motdepasse"}'

# Lister les tickets
curl http://localhost:8000/tickets \
  -H "Authorization: Bearer <access_token>"

# Créer un ticket
curl -X POST http://localhost:8000/tickets \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Problème imprimante", "content": "L imprimante du bureau 12 ne répond plus.", "urgency": 3, "type": 1}'
```

La documentation interactive est disponible sur `http://localhost:8000/docs`.

---

## Dépendances

| Package | Version | Rôle |
|---------|---------|------|
| fastapi | 0.115.0 | Framework web |
| uvicorn | 0.30.6 | Serveur ASGI |
| httpx | 0.27.2 | Client HTTP async |
| pydantic | 2.9.2 | Validation des données |
| pydantic-settings | 2.5.2 | Gestion de la configuration |
| python-jose | 3.3.0 | JWT |
| ldap3 | 2.9.1 | Authentification LDAP/AD |
| python-multipart | 0.0.12 | Données de formulaire |
| slowapi | 0.1.9 | Rate limiting |
