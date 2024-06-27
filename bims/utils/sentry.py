import logging

logging.basicConfig(level=logging.INFO)

def before_send(event, hint):
    logging.info(f"Processing event: {event}")
    logging.info(f'hint: {hint}')
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        logging.info(f"exc_type: {str(exc_value)}")
        if 'easyaudit.signals.model_signals.pre_save' in str(exc_value):
            logging.info("Ignoring easyaudit.signals.model_signals.pre_save error")
            return None
    return event