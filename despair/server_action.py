from despair.connection import RemoteConnection
import re

despair_group = "despair"
prefix = "19"


class ServerAction:
    def __init__(self, server):
        self.server = server
        self.connection = RemoteConnection(server)

    def changeChainDefaultPolicy(self, table, chain, policy):
        self.__exec(f' iptables -t {table} -P {chain} {policy}', sudo=True)

    def restoreIptables(self, text):
        self.__exec(f' cat | iptables-restore -n', input=text, sudo=True)

    def createIpset(self, name, options):
        self.__exec(f'ipset create -exist {name} {options}', sudo=True)

    def restoreIpset(self, content):
        self.__exec(f' cat | ipset restore', input=content, sudo=True)

    def flushIpset(self, name):
        self.__exec(f'ipset flush {name}', sudo=True)

    def cleanRepositories(self):
        self.__exec(f'rm -rf /etc/apt/sources.list.d/{prefix}*', sudo=True)
        self.__exec(f'rm -rf /etc/apt/preferences.d/{prefix}*', sudo=True)

    def syncRepository(self, repository, alias, priority=None):
        self.__exec(f'echo "{repository}" > /etc/apt/sources.list.d/{prefix}-{alias}.list', sudo=True)
        if priority:
            text = f'''Package: *
Pin: release a={alias}
Pin-Priority: {priority}
'''
            self.__exec(f'cat > /etc/apt/preferences.d/{prefix}-{alias}', input=text, sudo=True)

    def syncContent(self, path, content, owner=None, group=None, permissions=None):
        self.__exec(f"cat > {path}", input=content, sudo=True)
        if owner:
            self.__exec(f"chown {owner} {path}", sudo=True)
        if group:
            self.__exec(f"chgrp {group} {path}", sudo=True)
        if permissions:
            self.__exec(f"chmod 0{permissions} {path}", sudo=True)

    def __exec(self, cmd, sudo=False, input=None, sudo_user=None, quiet=False):
        result = self.connection.executeRemoteCommand(cmd, input=input, sudo=sudo, sudo_user=sudo_user)
        if not result.ok():
            print(f'Error while executing command: {cmd}')
            print(str(result))
        elif not quiet:
            print("SUCCESS!")
            print(result.out())
        return result

    def aptGetUpdate(self):
        self.__exec(f"apt-get update -qq", sudo=True)

    def syncPackages(self, packages, repository=None, environment=None):
        oneline = self.__package_oneline(packages)

        (to_install, to_remove) = self.__resolve_packages(packages, oneline)
        env = self.__make_env(environment)
        if to_install:
            install_string = self.__package_oneline(to_install, with_version=True)
            result = self.__exec(f'{env} apt-get install -qqy {f"-t {repository}" if repository else ""} {install_string}', sudo=True)
        else:
            print(f"Nothing to install from requested: {oneline}")

    def __make_env(self, environment):
        env = ''
        if environment:
            env = ' '.join(f'{key}={value}' for (key, value) in environment.items())
        return env

    def __package_oneline(self, packages, with_version=False):
        packs = []
        for package in packages:
            if type(package) is dict and "version" in package and with_version:
                packs.append(f'{package["name"]}={package["version"]}')
            elif type(package) is dict:
                packs.append(package["name"])
            else:
                packs.append(package)
        return " ".join(packs)

    def __resolve_packages(self, packages, package_oneline):
        package_info = PackageInfo(self.__exec(f'apt list -qqa {package_oneline} 2>/dev/null', quiet=True).out())
        to_install = []
        to_remove = []
        for package in packages:
            if type(package) is dict:
                name = package["name"]
            else:
                name = package
            if not package_info.is_installed(name):
                to_install.append(package)

        return (to_install, to_remove)


    def syncManagedGroup(self):
        return self.syncGroup(despair_group, True)

    def syncGroup(self, group, system=False):
        print(f'Syncing group {group} on {self.connection}')
        userExists = self.__exec(f'getent group {group}')
        if not userExists.out():
            if system:
                sys_switch = "--system"
            else:
                sys_switch = ""
            return self.__exec(f'addgroup {sys_switch} {group}', sudo=True)

    def sync_user(self, user):
        print(f'Syncing user {user} on {self.connection}')
        userExists = self.__exec(f'id {user}')
        if not userExists:
            return self.__exec(f'adduser --disabled-password --gecos "" -q {user}', sudo=True)

    def syncUserShell(self, user, shell):
        print(f'Syncing user\'s {user} shell on {self.connection}')
        out = self.__exec(f'getent passwd {user} | cut -d: -f7').out()
        if out != shell:
            self.__exec(f'usermod --shell {shell} {user}', sudo=True)

    def syncUserGroup(self, user, group):
        print(f'Syncing user primary group {user} on {self.connection}')
        is_the_same = self.__exec(f'id -gn {user}', sudo=True)
        if group != is_the_same.out():
            self.__exec(f'usermod -g {group} {user}', sudo=True)

    def syncUserGroups(self, user, groups):
        print(f'Syncing user secondary groups {user} on {self.connection}')
        is_the_same = self.__exec(f'id -Gn {user}', sudo=True)
        groups.append(despair_group)
        groups.append(user)
        difference = (set(groups)).symmetric_difference(set(is_the_same.out().split()))
        if difference:
            self.__exec(f'usermod -G {",".join(groups)} {user}', sudo=True)

    def updateKey(self, user, keys):
        print(f'Updating keys for {user} on {self.connection}')
        return self.__exec(f'cd ~{user} && umask 0077 && mkdir -p .ssh && cat > .ssh/authorized_keys', input=keys,
                           sudo=True, sudo_user=user)

    def updateMainKey(self, user, keys):
        print(f'Updating main key for {user} on {self.connection}')
        return self.__exec(f'umask 0077 && mkdir -p .ssh && cat > .ssh/authorized_keys', input=keys)

    def hostname(self, hostname):
        self.__exec(f'''hostnamectl set-hostname {hostname}''', sudo=True)

    def cloudHostname(self, hostname):
        self.__exec(f'''echo "hostname: {hostname}" > /etc/cloud/cloud.cfg.d/{prefix}_hostname.cfg''', sudo=True)
        self.hostname(hostname)

    def cleanSudoers(self):
        self.__exec(f'rm -rf /etc/sudoers.d/{prefix}* "', sudo=True)

    def becomeSudoer(self, sudoer):
        print(f'{sudoer} becomes sudoer on {self.connection}')
        self.__exec(
            f"echo '{sudoer} ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/{prefix}-{sudoer}-auto && chmod 0440 /etc/sudoers.d/{prefix}-{sudoer}-auto",
            sudo=True)

    def becomeMainSudoer(self, user):
        if self.__checkHasSudo(user):
            return
        print(f'{user} becomes sudoer on {self.connection}')
        return self.__exec(
            f'''su - -c "echo '{user} ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/{prefix}-{user}-auto && chmod 0440 /etc/sudoers.d/{prefix}-{user}-auto"''')

    def __checkHasSudo(self, user):
        result = self.__exec(f'''sudo id >/dev/null 2>/dev/null && echo True || echo False''').out()
        return result == "True"

    def __str__(self):
        return self.connection


class AllServersAction:
    def __init__(self, servers):
        self.servers = servers

    def sudoerReport(self):
        for key, value in self.servers.items():
            connection = RemoteConnection(value)
            print(
                "##########################################################################################################")
            print(f'### {key} {connection}')
            print(
                "##########################################################################################################")
            out = connection.executeRemoteCommand("getent passwd | cut -f1 -d: | sort | sudo xargs -L1 sudo -l -U")
            users = []
            for text in out.out():
                match = re.match(r'User (\S+) is not allowed to run sudo', text)
                if match:
                    users.append(match.group(1))
                else:
                    print(text, end='')
            print('All users: ', ','.join(sorted(users)))

class PackageInfo:
    def __init__(self, str):
        info = {}
        self.info = info
        for line in str.splitlines():
            list = line.split()
            try:
                options = ''
                if len(list) == 3:
                    (namepack, version, arch) = list
                elif len(list) == 4:
                    (namepack, version, arch, options) = list
                name = namepack.split('/')[0]
                if not name in info:
                    info[name] = {}
                    info[name]["versions"] = []
                info[name]["versions"].append(version)
                if options and "installed" in options:
                    info[name]["installed"] = True
                    info[name]["installed_version"] =version
            except Exception as e:
                print("Error while parsing response: ", line)


    def is_installed(self, name):
        if name in self.info and "installed" in self.info[name] and self.info[name]["installed"]:
            return True
        else:
            return False

    def installed_version(self,name):
        if name in self.info and self.info[name]["installed"]:
            return self.info[name]["installed_version"]
