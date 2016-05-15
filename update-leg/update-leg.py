#!/usr/bin/env python3
import sys
import os
import syslog
try:
    import requests
except ImportError:
    sys.stderr.write('Failed to import requests. You should probably run something such as:\n')
    sys.stderr.write('  pip install requests\n')
    sys.exit(1)

LEG_URL = 'https://{}/api/v3/bonds/{}/dhcp_legs/{}/'

def update_link_mode(bond_id, leg_id, link_mode, mgmt_server, auth, verify_ssl):
    """Update the specified leg to the given link mode."""
    res = requests.patch(
        LEG_URL.format(mgmt_server, bond_id, leg_id),
        json={'link_mode': link_mode},
        auth=auth,
        verify=verify_ssl
    )
    res.raise_for_status()

if __name__ == '__main__':
    syslog.openlog(ident='enable-disable-leg')

    try:
        bond_id = sys.argv[1]
        leg_id = sys.argv[2]
        link_mode = sys.argv[3]
    except IndexError:
        sys.stderr.write('Usage: {} <bond-id> <leg-id> offline|idle|active\n'.format(sys.argv[0]))
        sys.exit(1)

    try:
        mgmt_server = os.environ['BA_HOST']
        auth = (os.environ['BA_USER'], os.environ['BA_PASSWD'])
        verify_ssl = os.environ.get('BA_VERIFY_SSL', '') != 'False'
    except KeyError:
        sys.stderr.write('Missing one or more of these environment variables: BA_HOST, BA_USER and BA_PASSWD\n')
        sys.exit(1)

    try:
        update_link_mode(bond_id, leg_id, link_mode, mgmt_server, auth, verify_ssl)
        syslog.syslog('Updated bond {} leg {} link mode to {}.'.format(bond_id, leg_id, link_mode))
    except requests.exceptions.HTTPError as err:
        sys.stderr.write('Request failed: {}\n'.format(err.response.json()))
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        sys.stderr.write('Request to {} failed: {}\n'.format(mgmt_server, err))
        sys.exit(1)
