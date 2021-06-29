import logging

_LOG_PATH = 'alakazam.log'

logger = logging.getLogger('alakazam')


def init_logger():
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', '%d/%m/%Y %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(_LOG_PATH)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
