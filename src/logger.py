import json
import logging
import os

def logger():
    with open('config.json', 'r', encoding='utf-8') as file:
        cfg = json.load(file)

    if not cfg.get('logging_enabled', True):
        logging.disable(logging.CRITICAL)
        return logging.getLogger("logs")

    log_file = cfg.get('log_file', 'logs.log')
    os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)

    logging.basicConfig(filename=log_file, level=cfg.get('log_level', 'INFO').upper(), 
                        format='%(asctime)s - %(levelname)s - %(message)s',force=True)
    return logging.getLogger('logs')
