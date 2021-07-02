from cnc_server import CNCServer
from logger import init_logger

cnc = CNCServer()


def main():
    init_logger()
    cnc.start()


if __name__ == '__main__':
    main()
