import requests
from app.config import GLPI_API_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN

TIMEOUT = 15


class GLPIClient:
    def __init__(self):
        self.api_url = GLPI_API_URL
        self.app_token = GLPI_APP_TOKEN
        self.user_token = GLPI_USER_TOKEN
        self.session_token = None
        self.headers = {
            "App-Token": self.app_token,
            "Content-Type": "application/json",
        }

    def init_session(self):
        """Initialise une session GLPI et retourne le session_token."""
        url = f"{self.api_url}/initSession"
        headers = {
            **self.headers,
            "Authorization": f"user_token {self.user_token}",
        }
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        self.session_token = data.get("session_token")
        self.headers["Session-Token"] = self.session_token
        return data

    def kill_session(self):
        """Ferme la session GLPI active."""
        if not self.session_token:
            return
        url = f"{self.api_url}/killSession"
        requests.get(url, headers=self.headers, timeout=TIMEOUT)
        self.session_token = None

    def get_my_profiles(self):
        """Récupère tous les profils associés à l'utilisateur connecté."""
        url = f"{self.api_url}/getMyProfiles"
        response = requests.get(url, headers=self.headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_active_profile(self):
        """Récupère le profil actif de l'utilisateur connecté."""
        url = f"{self.api_url}/getActiveProfile"
        response = requests.get(url, headers=self.headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_my_entities(self, is_recursive=False):
        """Récupère toutes les entités accessibles par l'utilisateur."""
        url = f"{self.api_url}/getMyEntities"
        params = {"is_recursive": str(is_recursive).lower()}
        response = requests.get(
            url, headers=self.headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def get_active_entities(self):
        """Récupère les entités actives de l'utilisateur connecté."""
        url = f"{self.api_url}/getActiveEntities"
        response = requests.get(url, headers=self.headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_full_session(self):
        """Récupère les informations complètes de la session PHP."""
        url = f"{self.api_url}/getFullSession"
        response = requests.get(url, headers=self.headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_glpi_config(self):
        """Récupère la configuration globale de GLPI."""
        url = f"{self.api_url}/getGlpiConfig"
        response = requests.get(url, headers=self.headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def get_item(self, item_type, item_id, expand_dropdowns=False, with_logs=False):
        """Récupère un élément GLPI par son type et son ID."""
        url = f"{self.api_url}/{item_type}/{item_id}"
        params = {}
        if expand_dropdowns:
            params["expand_dropdowns"] = "true"
        if with_logs:
            params["with_logs"] = "true"
        response = requests.get(
            url, headers=self.headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def get_items(self, item_type, limit=50, offset=0, sort=1, order="ASC",
                  expand_dropdowns=False, only_id=False):
        """Récupère une collection d'éléments GLPI par type."""
        url = f"{self.api_url}/{item_type}"
        params = {
            "range": f"{offset}-{offset + limit - 1}",
            "sort": sort,
            "order": order,
        }
        if expand_dropdowns:
            params["expand_dropdowns"] = "true"
        if only_id:
            params["only_id"] = "true"
        response = requests.get(
            url, headers=self.headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def get_sub_items(self, item_type, item_id, sub_item_type, limit=50, offset=0):
        """Récupère les sous-éléments d'un élément GLPI."""
        url = f"{self.api_url}/{item_type}/{item_id}/{sub_item_type}"
        params = {
            "range": f"{offset}-{offset + limit - 1}",
        }
        response = requests.get(
            url, headers=self.headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def search_items(self, item_type, criteria=None, limit=50, offset=0,
                     sort=1, order="ASC", forcedisplay=None):
        """Recherche des éléments via le moteur de recherche GLPI."""
        url = f"{self.api_url}/search/{item_type}"
        params = {
            "range": f"{offset}-{offset + limit - 1}",
            "sort": sort,
            "order": order,
        }
        if criteria:
            for i, criterion in enumerate(criteria):
                for key, value in criterion.items():
                    params[f"criteria[{i}][{key}]"] = value
        if forcedisplay:
            for i, col in enumerate(forcedisplay):
                params[f"forcedisplay[{i}]"] = col
        response = requests.get(
            url, headers=self.headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def create_item(self, item_type, data):
        """Crée un ou plusieurs éléments dans GLPI."""
        url = f"{self.api_url}/{item_type}"
        response = requests.post(
            url, json={"input": data}, headers=self.headers, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def update_item(self, item_type, item_id, data):
        """Met à jour un élément existant dans GLPI."""
        url = f"{self.api_url}/{item_type}/{item_id}"
        response = requests.put(
            url, json={"input": data}, headers=self.headers, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def delete_item(self, item_type, item_id, force_purge=False):
        """Supprime un élément dans GLPI."""
        url = f"{self.api_url}/{item_type}/{item_id}"
        params = {}
        if force_purge:
            params["force_purge"] = "true"
        response = requests.delete(
            url, headers=self.headers, params=params, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
