import logging
import logging.handlers
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging() -> None:
    """
    Configure le logging de l'application :
    - Fichier rotatif JSON  → compatible Loki/Promtail
    - Console               → format lisible pour le développement

    La rotation se fait à 10 Mo, avec 5 fichiers conservés (soit ~50 Mo max).
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )

    # -- Handler fichier JSON rotatif --
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 Mo
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)

    # -- Handler console (format lisible) --
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )

    # -- Logger racine de l'application --
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)
    app_logger.propagate = False
