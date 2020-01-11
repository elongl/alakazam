import datetime
import os

OUTPUT_DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output')


def generate_product_path(description, extension=None):
    now = datetime.datetime.now().strftime('%m-%d-%Y-%H-%M-%S')
    return os.path.join(OUTPUT_DIR_PATH, f'{description}.{now}.{extension if extension else str()}')
