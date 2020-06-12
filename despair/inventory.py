import yaml

class Inventory:
    """
    inventory.yml
    """
    def __init__(self, path = 'inventory.yml'):
        with open(path) as f:
            self.data = yaml.load(f, Loader=yaml.FullLoader)
    
    def allServers(self):
        return self.data["servers"]
    
    def server(self, serverAlias):
        server = self.allServers()[serverAlias]
        server.update({"alias": serverAlias})
        return server
    
    def mainKey(self):
        return self.data["default"]["main-key"]
