from logger import init_logger
from server import CNCServer

cnc_server = CNCServer()


def main():
    init_logger()
    cnc_server.start()


if __name__ == '__main__':
    main()
