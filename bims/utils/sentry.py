import logging

logging.basicConfig(level=logging.INFO)


def before_send(event, hint):
    logging.info(f"Processing event: {event}")
    logging.info(f'Hint: {hint}')

    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        logging.info(f"Exception type: {exc_type}")
        logging.info(f"Exception value: {exc_value}")
        log_entry = ''

        if 'logentry' in event:
            if 'message' in event['logentry']:
                log_entry = event['logentry']['message']

        if (
                exc_value and
                (
                    "easy audit had a pre_save exception" in str(exc_value) or
                    "easy audit had a pre_save exception" in log_entry
                )
        ):
            logging.info("Ignoring 'easy audit had a pre_save exception.' error")
            return None

        if (
            exc_value and
            '400 Client Error: Bad Request for url:' in str(exc_value)
        ):
            logging.info("Ignoring '400 Client Error: Bad Request for url:' error")
            return None

        if 'easyaudit.signals.model_signals' in str(exc_value):
            logging.info("Ignoring easyaudit.signals.model_signals error")
            return None

    return event


def before_breadcrumb(crumb, hint):
    if crumb.get('category') == 'http':
        if crumb.get('data', {}).get('status_code') == 200:
            return None

    return crumb
