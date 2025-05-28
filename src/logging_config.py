import logging
import sys
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = "app.log"

def setup_logging(console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Configures advanced logging for the application.

    Logs will be output to stdout and to a rotating log file.

    Args:
        console_level (int, optional): Logging level for console output. Defaults to logging.INFO.
        file_level (int, optional): Logging level for file output. Defaults to logging.DEBUG.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except OSError as e:
            # Fallback to basic console logging if directory creation fails
            logging.basicConfig(level=console_level, 
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
            logging.error(f"Impossibile creare la directory dei log {LOG_DIR}: {e}. Logging su file disabilitato.")
            return

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%H:%M:%S' 
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotating)
    log_file_path = os.path.join(LOG_DIR, LOG_FILE)
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3, 
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s:%(module)s:%(lineno)d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info("Logging configurato (Console: %s, File: %s)", 
                logging.getLevelName(console_level), 
                logging.getLevelName(file_level))


if __name__ == '__main__':
    setup_logging(console_level=logging.DEBUG, file_level=logging.DEBUG)
    
    # Test various loggers
    root_logger = logging.getLogger()
    module_logger = logging.getLogger("mioModuloSpecifico")

    root_logger.debug("Questo è un messaggio di debug (root).")
    root_logger.info("Questo è un messaggio informativo (root).")
    root_logger.warning("Questo è un avviso (root).")
    root_logger.error("Questo è un errore (root).")
    root_logger.critical("Questo è un errore critico (root).")

    module_logger.debug("Questo è un messaggio di debug (mioModuloSpecifico).")
    module_logger.info("Questo è un messaggio informativo (mioModuloSpecifico).")
    
    # Test log rotation (manual trigger would be complex here, but configuration is set)
    # For a real test, you would need to log more than maxBytes.
    root_logger.info(f"I log verranno salvati in: {os.path.abspath(os.path.join(LOG_DIR, LOG_FILE))}") 