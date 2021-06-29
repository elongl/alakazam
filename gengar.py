import socket
import struct
from dataclasses import dataclass
from logging import log

from logger import logger


class CommandTypes:
    ECHO = 0
    SHELL = 1


INT_SIZE = 4


@dataclass
class Gengar:
    sock: socket.socket
    host: str

    def echo(self, text: str):
        logger.info(f'Echoing: {text}')
        self.sock.send(struct.pack('I', CommandTypes.ECHO) + struct.pack('I', len(text)) + text.encode())
        logger.info(f'Received from echo: {self.sock.recv(len(text)).decode()}')

    def shell(self, cmd: str):
        logger.info(f'Running: {cmd}')
        self.sock.send(struct.pack('I', CommandTypes.SHELL) + struct.pack('I', len(cmd)) + cmd.encode())
        exit_code = struct.unpack('i', self.sock.recv(INT_SIZE))[0]
        if exit_code == -1:
            logger.error('Gengar failed to execute the shell command.')
            return
        output_size = struct.unpack('I', self.sock.recv(INT_SIZE))
        logger.info(f'Command output ({exit_code}): {self.sock.recv(output_size)}')
