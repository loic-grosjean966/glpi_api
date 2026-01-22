import requests
from app.config import GLPI_API_URL, GLPI_APP_TOKEN, GLPI_USER_TOKEN

class GLPIClient:
    def __init__(self):
        self.api_url = GLPI_API_URL
        self.app_token = GLPI_APP_TOKEN
        self.user_token = GLPI_USER_TOKEN
        self.headers = {
            "App-Token": self.app_token,
            "Authorization": f"user_token {self.user_token}",
            "Content-Type": "application/json"
        }

    def get_items(self, item_type):
        url = f"{self.api_url}/search/{item_type}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_item(self, item_type, data):
        url = f"{self.api_url}/{item_type}"
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()