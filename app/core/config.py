from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GLPI
    GLPI_URL: str
    GLPI_USER_TOKEN: str
    GLPI_APP_TOKEN: str

    # LDAP / AD
    LDAP_HOST: str        # IP ou FQDN du contrôleur de domaine
    LDAP_DOMAIN: str      # Nom de domaine AD pour le UPN (ex: domaine.local)
    LDAP_PORT: int = 389
    LDAP_BASE_DN: str
    LDAP_BIND_USER: str
    LDAP_BIND_PASSWORD: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30       # access token : 30 min
    JWT_REFRESH_EXPIRE_DAYS: int = 30  # refresh token : 30 jours

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/glpi_api.log"

    class Config:
        env_file = ".env"


settings = Settings()
