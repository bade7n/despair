from subprocess import Popen, PIPE, STDOUT, call, run, CompletedProcess
import os

verbose = 0
ssh_bin = '/usr/local/bin/ssh'


class RemoteConnection:
    """
    Basic methods to connect to servers, supports interactive and non-interactive ways.
    """

    def __init__(self, server, identity_key_path='identity_key'):
        self.server = server
        self.connection = self.__sshConnectionString()
        self.identity_key_path = identity_key_path
        pass

    def __sshConnectionString(self):
        return self.server["user"] + '@' + self.server["ip"]

    def execRemoteInteractiveCommand(self, cmd, input=None, capture_output=False):
        if verbose:
            print(f"Executing interactive command: {cmd}")
        command = self.__remoteInteractiveSshCommand(cmd)
        return CommandResult(run(command, input=input.encode(), capture_output=capture_output))

    def __remoteCommand(self, text):
        port = 22
        if "port" in self.server:
            port = self.server["port"]
        return [ssh_bin, '-p', f'{port}', '-i', self.identity_key_path, self.connection, text]

    def __remoteInteractiveSshCommand(self, text):
        command = self.__remoteCommand(text)
        command.insert(1, '-t')
        return command

    def executeRemoteCommand(self, cmd, input=None, sudo=False, sudo_user=None):
        if sudo:
            cmd = cmd.replace('"', r'\"')
            if sudo_user:
                cmd = f'sudo -u {sudo_user} bash -c "{cmd}"'
            else:
                cmd = f'sudo bash -c "{cmd}"'
        print(f'$$$$$ {cmd} in {self.connection}')
        command = self.__remoteCommand(cmd)
        return self.__execRemoteCommand(command, input)

    def __execRemoteCommand(self, command, data):
        if verbose:
            print(f"Executing command: {command} with input {data}")
        app = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True, bufsize=1)
        out = app.communicate(input=data)
        if out[1]:
            print(f'''
    Error while executing command {command}
    Stdout: {out[0]} 
    Stderr: {out[1]}
    ''')
        return CommandResult(out)

    def __str__(self):
        return self.connection


class CommandResult:
    def __init__(self, out):
        if type(out) is CompletedProcess:
            self.is_ok = out.returncode == 0
            self.returncode = out.returncode
            self.stdout = out.stdout.decode()
            self.stderr = out.stderr.decode()
        else:
            self.is_ok = not out[1]
            self.returncode = -1
            self.stdout = out[0]
            self.stderr = out[1]


    def out(self):
        return self.stdout.strip()

    def err(self):
        return self.stderr

    def __str__(self):
        return f'Stdout: {self.stdout}\nStderr:{self.stderr}'

    def ok(self):
        return self.is_ok

    def __bool__(self):
        return not self.stderr

    __nonzero__ = __bool__
