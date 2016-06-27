# swap-connected-ip.py

This script uses the Bonded Internet management server API to disable a connected IP on one bond and enable a connected IP on another bond. This can be used in a high availability environment (i.e. keepalived) to move an IP from a primary device to a standby device should the primary device fail.

## Requirements

* A Bonded Internet management server
* A user account on the server with permission to view and update connected IPs. We recommend a dedicated group and user for this, so that the account used to move IPs has the fewest permissions needed to do so.
* Python (version 3 preferred, but 2 should work as well)
* [requests](http://python-requests.org) (Python library for making HTTP requests)

## Installation

Download the latest version from GitHub to /usr/local/bin/:

```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/multappliednetworks/api-examples/master/swap-connected-ip/swap-connected-ip.py -O swap-connected-ip.py
sudo chmod +x swap-connected-ip.py
```
Install the Requests Python library:

```
sudo pip install --upgrade requests
```

## Usage

TODO: an example keepalived config should go here



```
[bondingadmin]
host
user
passwd
verify_ssl
```
