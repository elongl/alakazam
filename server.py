import logging
import socket
import threading

from gengar import Gengar


class CNCServer:
    DEFAULT_PORT = 5000
    gengars = []

    def __init__(self, port=DEFAULT_PORT):
        self.sock = socket.socket()
        self.port = port

    def start(self):
        logging.info(f'Starting the CNC server at :{self.port}')
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen()
        threading.Thread(target=self.accept_forever, daemon=True).start()

    def accept_forever(self):
        while True:
            logging.info('Waiting for connections.')
            gengar_sock, (gengar_host, _) = self.sock.accept()
            logging.info(f'Received Gengar connection @ {gengar_host}')
            self.gengars.append(Gengar(gengar_sock, gengar_host))
