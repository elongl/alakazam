import logging

_LOG_PATH = 'alakazam.log'
_FORMAT = '%(asctime)s %(message)s'
_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'


def init_logger():
    logging.basicConfig(format=_FORMAT, datefmt=_DATE_FORMAT, level=logging.DEBUG)
    log_formatter = logging.Formatter(_FORMAT, _DATE_FORMAT)
    file_handler = logging.FileHandler(_LOG_PATH)
    file_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(file_handler)

    logging.getLogger('asyncio').setLevel(logging.WARNING)
