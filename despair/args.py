import argparse

def argumentParser():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-r", "--report", action="store_true", help="Get a sudoer report from the inventory")
    group.add_argument("-k", "--authorized-keys", type=str, help="Update server authorized_keys according to the inventory")
    group.add_argument("--init", type=str, help="Initialize server configuration (hostname, main_key, become_sudoer)")
    parser.add_argument("-v", "--verbose", help="more output information", action="store_true")
    parser.add_argument("-c", "--clean", help="clean existing data and create new (cleans sudoers)", action="store_true")
    parser.add_argument("-u", "--users", help="syncronize users", type=str)
    parser.add_argument("-t", "--tasks", help="syncronization tasks (repositories, packages, custom scripts)", type=str)
    parser.add_argument("--network", help="syncronization network: iptables/ipsets", type=str)
    parser.add_argument("-a", "--all", help="syncronize everything: users, repositories, packages, authorization_keys without initialization", type=str)
    parser.add_argument("-i", "--identity-key", help="ssh connection identity path", type=str)
    return parser.parse_args()