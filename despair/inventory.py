import yaml
from .server_action import ServerAction, AllServersAction
import subprocess
import os
from pathlib import Path

class Inventory:
    """
    inventory.yml
    """
    def __init__(self, path='inventory.yml'):
        self.inventory_path = path
        with open(path) as f:
            self.data = yaml.load(f, Loader=yaml.FullLoader)
    
    def allServers(self):
        return self.data["inventory"]["servers"]
    
    def server(self, serverAlias):
        server = self.allServers()[serverAlias]
        server.update({"alias": serverAlias, "public_key": self.__get_public_key()})
        return server

    def __mainKey(self):
        paths = self.data["inventory"]["identity_key"]
        keys = paths.split(',')
        inventory_path = Path(self.inventory_path).parent
        for key_name in keys:
            if (inventory_path / key_name).exists():
                return str((inventory_path / key_name).absolute())
        raise Exception(f'identity_keys are not found under the path {inventory_path} and by name: {paths}')

    def __get_public_key(self):
        identity_key = self.__mainKey()
        public_key = subprocess.run(f'ssh-keygen -y -f {identity_key}', shell=True, capture_output=True)
        return public_key.stdout.decode()

    def server_action(self, server_name):
        server = self.server(server_name)
        return ServerAction(server, self.__mainKey())
