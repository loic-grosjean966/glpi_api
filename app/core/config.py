from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GLPI
    GLPI_URL: str = "http://172.16.8.22/apirest.php"
    GLPI_USER_TOKEN: str
    GLPI_APP_TOKEN: str

    # LDAP / AD
    LDAP_HOST: str = "lecreusot.priv"
    LDAP_PORT: int = 389
    LDAP_BASE_DN: str = "dc=lecreusot,dc=priv"
    LDAP_BIND_USER: str  # ex: CN=svc-api,OU=Services,DC=lecreusot,DC=priv
    LDAP_BIND_PASSWORD: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8h

    class Config:
        env_file = ".env"


settings = Settings()
