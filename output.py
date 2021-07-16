import os
from datetime import datetime

from logger import logger

_OUTPUT_DIR_PATH = 'output'

_DATETIME_FORMAT = '%d-%m-%Y-%H-%M'


def create_output_dir():
    try:
        os.mkdir(_OUTPUT_DIR_PATH)
        logger.debug('Created an output directory.')
    except FileExistsError:
        pass


def generate_path(file_path: str):
    return os.path.join(_OUTPUT_DIR_PATH, f'{datetime.now().strftime(_DATETIME_FORMAT)}-{file_path}')
