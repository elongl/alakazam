from cnc_server import CNCServer
from logger import init_logger



def main():
    global cnc
    cnc = CNCServer()
    init_logger()
    cnc.start()


if __name__ == '__main__':
    main()
