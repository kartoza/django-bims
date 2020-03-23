import json
import logging
import inspect

logger = logging.getLogger('bims')


def log(message, log_type='info', caller=None):
    """
    Log the message with the function that called it
    :param message: log message
    :param caller: function caller name
    :param log_type: log type
    :return:
    """
    if not caller:
        caller = inspect.stack()[1][3]
    logger_function = getattr(logger, log_type)
    try:
        message = message.encode('utf-8')
    except ValueError:
        message = message
    except AttributeError:
        message = json.dumps(message)
    logger_function('{caller} : {message}'.format(
        caller=caller,
        message=message
    ))
