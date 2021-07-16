import socket
import threading

from gengar import Gengar, GengarAuthenticationFailed
from logger import logger


class CNCServer:
    DEFAULT_PORT = 5000
    _gengars = []

    def __init__(self, port=DEFAULT_PORT):
        self.sock = socket.socket()
        self.port = port

    @property
    def gengars(self):
        return set([gengar for gengar in self._gengars if gengar.alive])

    @property
    def dead_gengars(self):
        return set([gengar for gengar in self._gengars if not gengar.alive])

    def assure_gengars_connected(self):
        for gengar in self.gengars:
            gengar.echo('Sync')

    def start(self):
        logger.info(f'Starting the CNC server at :{self.port}')
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen()
        threading.Thread(target=self.accept_forever, daemon=True).start()

    def accept_forever(self):
        logger.info('Waiting for connections.')
        while True:
            gengar_sock, (gengar_host, _) = self.sock.accept()
            logger.info(f'Received Gengar connection @ {gengar_host}')
            gengar = Gengar(gengar_sock, gengar_host)
            try:
                gengar.auth()
                gengar.init()
                self._gengars.append(gengar)
            except GengarAuthenticationFailed:
                logger.error('Failed to authenticate Gengar.')
                gengar_sock.close()
            except ConnectionResetError:
                logger.error('Gengar disconnected during initialization.')
                gengar_sock.close()
