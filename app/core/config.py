from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GLPI
    GLPI_URL: str
    GLPI_USER_TOKEN: str
    GLPI_APP_TOKEN: str

    # LDAP / AD
    LDAP_HOST: str
    LDAP_PORT: int = 389
    LDAP_BASE_DN: str
    LDAP_BIND_USER: str
    LDAP_BIND_PASSWORD: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8h

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/glpi_api.log"

    class Config:
        env_file = ".env"


settings = Settings()
