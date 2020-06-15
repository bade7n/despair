# -*- coding: utf-8 -*-

__version__ = "0.0.1"

from .server_action import ServerAction, AllServersAction
from .inventory import Inventory
from .args import argumentParser
from .network import Network
import subprocess

clean = 0
inventory_path = 'inventory.yml'
identity_key = 'identity_key'


def main():
    global verbose
    global clean
    global identity_key

    args = argumentParser()
    if args.verbose:
        verbose = 1
    if args.clean:
        clean = 1
    if args.inventory:
        inventory_path = args.inventory
    if args.identity_key:
        identity_key = args.identity_key

    inventory = Inventory(inventory_path)

    if args.authorized_keys:
        server = inventory.server(args.authorized_keys)
        syncAuthorizedKeys(server)
    elif args.init:
        server = inventory.server(args.init)
        initServerConfiguration(inventory, server)
        syncUsers(server)
    elif args.all:
        server = inventory.server(args.all)
        syncAll(server)
    elif args.users:
        server = inventory.server(args.users)
        syncUsers(server)
    elif args.tasks:
        server = inventory.server(args.tasks)
        syncTasks(server)
    elif args.network:
        server = inventory.server(args.network)
        syncNetwork(server)
    elif args.report:
        AllServersAction(inventory.allServers()).sudoerReport()


def __server_action(server):
    global identity_key
    return ServerAction(server, identity_key)


def syncNetwork(server):
    if "network" in server:
        action = __server_action(server)
        net = Network(action, server["network"])
        net.sync()


def syncTasks(server):
    action = __server_action(server)
    __syncTasks(server, action)


def __syncTasks(server, action):
    if clean:
        action.cleanRepositories()
    for key, value in server.items():
        if key.endswith("_tasks"):
            __syncTask(key, value, action)


def __syncTask(key, value, action):
    print(f"Processing task {key}")
    update = True
    for task in value:
        if "packages" in task:
            if update:
                action.aptGetUpdate()
            update = False
            action.syncPackages(task["packages"],
                                repository=task["from-repository"] if "from-repository" in task else None,
                                environment=task["environment"] if "environment" in task else None)
        elif "content" in task and "path" in task:
            action.syncContent(task["path"], task["content"])
        elif "repository" in task:
            action.syncRepository(task["repository"], task["alias"] if "alias" in task else None,
                                  task["priority"] if "priority" in task else None)
            update = True
    if update:
        action.aptGetUpdate()


def syncAll(server):
    action = __server_action(server)
    __syncUsers(server, action)
    __syncAuthorizedKeys(server, action)
    __syncTasks(server, action)


def syncUsers(server):
    action = __server_action(server)
    __syncUsers(server, action)


def __syncUsers(server, action):
    if "users" in server:
        for user, user_info in server["users"].items():
            action.sync_user(user)
            if "group" in user_info:
                action.syncUserGroup(user, user_info["group"])
            if "shell" in user_info:
                action.syncUserShell(user, user_info["shell"])
            action.syncUserGroups(user, user_info["groups"] if "groups" in user_info else [])


def initServerConfiguration(inventory, server):
    action = __server_action(server)
    keys = __get_public_key()
    action.updateMainKey(server["user"], keys)
    action.syncManagedGroup()
    becomeSudoer(server, action, clean)
    if "cloud_hostname" in server:
        action.cloudHostname(server["cloud_hostname"])
    if "hostname" in server:
        action.hostname(server["hostname"])

def __get_public_key():
    global identity_key
    public_key = subprocess.run(f'ssh-keygen -y -f {identity_key}', shell=True, capture_output=True)
    return public_key.stdout.decode()


def becomeSudoer(server, action, clean):
    if clean:
        action.cleanSudoers()
    action.becomeMainSudoer(server["user"])
    if "sudoers" in server:
        for sudoer in server["sudoers"]:
            action.becomeSudoer(sudoer)


def syncAuthorizedKeys(server):
    action = __server_action(server)
    __syncAuthorizedKeys(server, action)


def __syncAuthorizedKeys(server, action):
    for rule in server["authorized_keys"]:
        keys = "\n".join(rule["keys"])
        for user in rule["remote-users"]:
            if user == server["user"]:
                keys += "\n" + __get_public_key()
            action.updateKey(user, keys)

