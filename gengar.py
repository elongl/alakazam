import logging
import socket
import struct
from dataclasses import dataclass


@dataclass
class Gengar:
    sock: socket.socket
    host: str

    def echo(self, text: str):
        logging.info(f'Echoing: {text}')
        self.sock.send(struct.pack('I', 0) + struct.pack('I', len(text)) + text.encode())
        logging.info(f'Received from echo: {self.sock.recv(len(text)).decode()}')
