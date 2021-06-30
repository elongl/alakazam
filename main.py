from logger import init_logger
from server import CNCServer

cnc = CNCServer()


def main():
    init_logger()
    cnc.start()


if __name__ == '__main__':
    main()
