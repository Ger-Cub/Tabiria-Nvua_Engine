import logging
import sys

def setup_logging():
    """
    Configure le format de journalisation standardisé pour Tabiria-Nvua Engine.
    """
    log_format = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Réduire le verbiage des bibliothèques tierces
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    
    logger = logging.getLogger("nvua_engine")
    logger.info("Logging initialisé pour Tabiria-Nvua Engine.")
    return logger

logger = setup_logging()
