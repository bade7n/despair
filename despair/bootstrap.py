# -*- coding: utf-8 -*-

__version__ = "0.0.1"

from .server_action import ServerAction, AllServersAction
from .inventory import Inventory
from .args import argumentParser
from .network import Network

clean = 0
inventory_path = 'inventory.yml'

def main():
    global verbose
    global clean

    args = argumentParser()
    if args.verbose:
        verbose = 1
    if args.clean:
        clean = 1
    if args.inventory:
        inventory_path = args.inventory

    inventory = Inventory(inventory_path)

    if args.authorized_keys:
        action = inventory.server_action(args.authorized_keys)
        syncAuthorizedKeys(action)
    elif args.init:
        action = inventory.server_action(args.init)
        initServerConfiguration(action)
    elif args.all:
        action = inventory.server_action(args.all)
        syncAll(action)
    elif args.users:
        action = inventory.server_action(args.users)
        __syncUsers(action)
    elif args.tasks:
        action = inventory.server_action(args.tasks)
        __syncTasks(action)
    elif args.network:
        action = inventory.server_action(args.network)
        syncNetwork(action)
    elif args.report:
        AllServersAction(inventory.allServers()).sudoerReport()



def syncNetwork(action):
    if "network" in action.server:
        net = Network(action, action.server["network"])
        net.sync()

def __syncTasks(action):
    if clean:
        action.cleanRepositories()
    for key, value in action.server.items():
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
        elif "script" in task:
            action.execScript(task["script"], task["sudo"] if "sudo" in task else None)
    if update:
        action.aptGetUpdate()

def syncAll(action):
    __syncUsers(action)
    __syncAuthorizedKeys(action)
    __syncTasks(action)

def __syncUsers(action):
    if "users" in action.server:
        for user, user_info in action.server["users"].items():
            action.sync_user(user)
            if "group" in user_info:
                action.syncUserGroup(user, user_info["group"])
            if "shell" in user_info:
                action.syncUserShell(user, user_info["shell"])
            action.syncUserGroups(user, user_info["groups"] if "groups" in user_info else [])

def initServerConfiguration(action):
    action.updateMainKey(action.server["user"], action.server["public_key"])
    action.becomeMainSudoer(action.server["user"])
    action.syncManagedGroup()
    becomeSudoer(action, clean)
    if "cloud_hostname" in action.server:
        action.cloudHostname(action.server["cloud_hostname"])
    if "hostname" in action.server:
        action.hostname(action.server["hostname"])

def becomeSudoer(action, clean):
    if clean:
        action.cleanSudoers()
    if "sudoers" in action.server:
        for sudoer in action.server["sudoers"]:
            action.becomeSudoer(sudoer)


def syncAuthorizedKeys(action):
    __syncAuthorizedKeys(action)

def __syncAuthorizedKeys(action):
    server = action.server
    for rule in server["authorized_keys"]:
        keys = "\n".join(rule["keys"])
        for user in rule["remote-users"]:
            if user == server["user"]:
                keys += "\n" + server["public_key"]
            action.updateKey(user, keys)

