import logging

logging.basicConfig(level=logging.INFO)


def before_send(event, hint):
    logging.info(f"Processing event: {event}")
    logging.info(f'Hint: {hint}')

    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        logging.info(f"Exception type: {exc_type}")
        logging.info(f"Exception value: {exc_value}")

        if exc_value and str(exc_value) == "easy audit had a pre-save exception.":
            logging.info("Ignoring 'easy audit had a pre-save exception.' error")
            return None

        if 'easyaudit.signals.model_signals' in str(exc_value):
            logging.info("Ignoring easyaudit.signals.model_signals error")
            return None

    return event
