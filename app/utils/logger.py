import os
import logging
from logging.handlers import RotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    
    handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, log_file),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger

system_logger = setup_logger('system', 'system.log')
activity_logger = setup_logger('activity', 'activity.log')
security_logger = setup_logger('security', 'security.log')
error_logger = setup_logger('errors', 'errors.log', level=logging.ERROR)
