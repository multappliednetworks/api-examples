#!/usr/lib/bonding/bin/python3
"""
Swap a connected IP from one bond to another.

If configured with role=master, disable the connected IP on the backup and enable it on the master. If configured with role=backup, disable on the master and enable on the backup.
"""
import sys
import os
import syslog
import configparser
import time
import requests # This is always installed in the /usr/lib/bonding/bin/python environment. If you use your own Python environment, install this with "pip3 install requests".

CONF_FILE = '/etc/bonding/swapconnectedip.conf'
CONNECTED_IP_URL = 'https://{}/api/v3/bonds/{}/connected_ips/{}/'
MASTER_PRIO = '10'

def update_connected_ip(target_ids, enabled, mgmt_server, auth, verify_ssl, timeout, attempts, attempt_delay):
    """Update the connected IP. Try multiple times if necessary."""
    for i in range(attempts):
        bond_id = target_ids[0]
        connected_ip_id = target_ids[1]
        log('Updating bond {} connected IP {} enabled to {} (attempt {} of {}).'.format(bond_id, connected_ip_id, enabled, i + 1, attempts))
        try:
            single_patch_connected_ip(bond_id, connected_ip_id, enabled, mgmt_server, auth, verify_ssl, timeout)
            log('Updated bond {} connected IP {}.'.format(bond_id, connected_ip_id))
            break
        except requests.exceptions.HTTPError as err:
            log('Request failed: {}'.format(err.response.json()))
            if err.response.status_code >= 400 and err.response.status_code < 500:
                # A client error occurred. No use retrying.
                break
        except requests.exceptions.RequestException as err:
            log('Request to {} failed: {}'.format(mgmt_server, err))
        if i < attempts - 1:
            # We will be trying again, so sleep. Don't sleep if that was the last try.
            time.sleep(attempt_delay)

def single_patch_connected_ip(bond_id, connected_ip_id, enabled, mgmt_server, auth, verify_ssl, timeout):
    """Enable or disable the specified connected IP."""
    res = requests.patch(
        CONNECTED_IP_URL.format(mgmt_server, bond_id, connected_ip_id),
        json={'enabled': enabled},
        auth=auth,
        verify=verify_ssl,
        timeout=timeout,
    )
    res.raise_for_status()

def log(message):
    """If running in a TTY, print the message to the screen, otherwise log it."""
    if sys.stdout.isatty():
        sys.stdout.write('{}\n'.format(message))
    else:
        syslog.syslog(message)

if __name__ == '__main__':
    syslog.openlog(ident='swap-connected-ip')

    try:
        with open(CONF_FILE, 'r') as cf:
            config = configparser.ConfigParser()
            config.read_file(cf)
    except EnvironmentError as e:
        log('Error: Failed to read conf file: {}'.format(e))
        sys.exit(1)

    # State refers to the newly-executed state in keepalived- MASTER when a node is active, BACKUP when it's not active.
    # Role refers to the purpose of the node- either the master node or the backup node.
    if len(sys.argv) >= 4:
        filename, instance, instance_id, state, prio = sys.argv
        role = 'master' if prio == MASTER_PRIO else 'backup'
    else:
        state = 'MASTER'
        role = 'master'
        log('Warning: not enough arguments to determine state and prio from argument list. Defaulting to state MASTER, prio 10 (master bonder). To run as backup, run:')
        log('{} arg arg MASTER 9'.format(sys.argv[0]))

    if state != 'MASTER':
        # Only the node going to MASTER state needs to do anything. If this node is going to BACKUP state, then we know that the other node will be going to MASTER, so we don't need to do anything.
        sys.exit(0)

    try:
        mgmt_server = config.get('bondingadmin', 'host')
        user = config.get('bondingadmin', 'user')
        passwd = config.get('bondingadmin', 'passwd')
        verify_ssl = config.getboolean('bondingadmin', 'verify_ssl', fallback=True)
        timeout = config.getfloat('bondingadmin', 'timeout', fallback=10.0)
        attempts = config.getint('bondingadmin', 'attempts', fallback=3)
        attempt_delay = config.getfloat('bondingadmin', 'attempt_delay', fallback=5.0)

        master_bond_id = config.get('bond', 'master_bond_id')
        master_connected_ip_id = config.get('bond', 'master_connected_ip_id')
        backup_bond_id = config.get('bond', 'backup_bond_id')
        backup_connected_ip_id = config.get('bond', 'backup_connected_ip_id')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        log('Error: incomplete configuration: {}'.format(e))
        sys.exit(1)
    except ValueError as e:
        log('Error: {}'.format(e))
        sys.exit(1)

    auth = (user, passwd)

    if role == 'master':
        # We're running on the master, so we need to disable on the backup and enable on the master.
        disable_target = (backup_bond_id, backup_connected_ip_id)
        enable_target = (master_bond_id, master_connected_ip_id)
    elif role == 'backup':
        # We're running on the backup, so we need to disable on the master and enable on the backup.
        disable_target = (master_bond_id, master_connected_ip_id)
        enable_target = (backup_bond_id, backup_connected_ip_id)
    else:
        log('Error: role must be either master or backup')
        sys.exit(1)

    # Disable the peer's connected IP, then enable our connected IP.
    update_connected_ip(disable_target, False, mgmt_server, auth, verify_ssl, timeout, attempts, attempt_delay)
    update_connected_ip(enable_target, True, mgmt_server, auth, verify_ssl, timeout, attempts, attempt_delay)
