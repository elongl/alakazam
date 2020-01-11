import os

from cnc_server import CNCServer
from output import OUTPUT_DIR_PATH


def assure_output_dir():
    try:
        os.mkdir(OUTPUT_DIR_PATH)
    except FileExistsError:
        pass


assure_output_dir()
cnc = CNCServer()
cnc.listen()
