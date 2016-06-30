# swap-connected-ip.py

This script uses the Bonded Internet management server API to disable a connected IP on one bond and enable a connected IP on another bond. This can be used in a high availability environment (i.e. keepalived) to move an IP from a primary device to a backup device should the primary device fail. It is meant to be called on the device taking over as the active CPE.

## Requirements

* A Bonded Internet management server
* A user account on the server with permission to view and update connected IPs. We recommend a dedicated group and user for this, so that the account used to move IPs has the fewest permissions needed to do so.
* 2 bonders with Bonded Internet >= 2016.1

## Installation

Download the latest version from GitHub to /usr/local/bin/:

```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/multappliednetworks/api-examples/master/swap-connected-ip/swap-connected-ip.py
sudo chmod +x swap-connected-ip.py
```

## Usage

Create two bonds. On each bond, create a duplicate connected IP- but the one on the primary should be enabled, and the one on the secondary should be disabled.

On both the master and backup CPEs, create a configuration file at ```/etc/keepalived/swap-connected-ip.conf```. Use the example below, replacing with your own values. The only value that should differ between the master and backup is the ```role``` field in the ```[node]``` section.

```
[bondingadmin]
host = bondingadmin.example.com
user = username
passwd = correct horse battery staple
verify_ssl = true # Defaults to true- you can omit this if you have a properly-signed SSL cert
timeout = 10.0 # Omit if you're OK with a 10 second request timeout
attempts = 3 # Omit if you're OK with 3 retries for each request
attempt_delay = 5.0 # Omit if you're OK with a delay of 5 seconds after a failed request

[bond]
# Set the object IDs on which to operate.
master_bond_id = 1
master_connected_ip_id = 1
backup_bond_id = 2
backup_connected_ip_id = 2

[node]
# TODO: if keepalived can be configured to provide this as an argument or an environment variable, it would make configuration much easier.
role = master # On the backup host, set to "backup"
```

After the configuration file is set up, you can call the script on the command line to test it:

```
/usr/local/bin/swap-connected-ip.py
```

The script will print a few lines about what it's doing and any errors it encounters.

When called from keepalived (or equivalent application), the script will log to the syslog file.

TODO: provide example keepalived configuration?
