
class Network:
    def __init__(self, action, network):
        self.action = action
        self.network = network
    
    def sync(self):
        self.action.syncPackages(["ipset"])
        if "ipsets" in self.network:
            self.__syncIpsets(self.network["ipsets"])
        if "iptables" in self.network:
            self.__syncIptables(self.network["iptables"])

    def __syncIpsets(self, ipsets):
        for key,value in ipsets.items():
            self.__updateSet(key, value)
            print(f'{key} {value}')

    def __syncIptables(self, iptables):
        for key,value in iptables.items():
            self.__updateTable(key, value)

    def __updateTable(self, table, value):
        text = f'*{table}\n'
        # generate list of chains
        for chain, val in value.items():
            if "skip" in val and "policy" in val:
                self.action.changeChainDefaultPolicy(table, chain, val["policy"])        
            else:
                text += f':{chain} {val["policy"] if "policy" in val else "-"} [0:0]\n'
        # flush chains
        for chain, val in value.items():
            if "skip" not in val and "flush" in val:
                text += f"-F {chain}\n"
        # rules part
        for chain, val in value.items():
            if "rules" in val and "skip" not in val:
                for rule in val["rules"]:
                    text += f'-A {chain} {rule} {"-j ACCEPT" if "-j" not in rule else ""}\n'
        text += "COMMIT\n"
        print(text)
        self.action.restoreIptables(text)

    def __updateSet(self, key, value):
        self.action.createIpset(key, value["options"])
        text = f'flush {key}\n'
        if "entries" in value:
            for entry in value["entries"]:
                text += f'add {key} {entry}\n'
        self.action.restoreIpset(text)
