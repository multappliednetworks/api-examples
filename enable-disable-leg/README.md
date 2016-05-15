# update-leg.py

This script uses the Bonded Internet management server API to change the link mode of a leg.

It can be used, for example, to set a leg to active mode during the night and idle mode during the day.

Available link modes are:

* Offline: The leg is not used for anything. The bonder will not bring up this interface at all.
* Idle: The leg is configured but not used for bonded traffic. This can be useful if you need to remove a poorly-performing leg from the bond but still want to run ping and throughput tests on it. The bonder may use this leg to connect to the management server.
* Active: The leg is configured and used for bonded traffic.

## Requirements

* A Bonded Internet management server
* A user account on the server with permission to update legs
* Python (version 3 preferred, but 2 should work as well)
* [requests](http://python-requests.org) (Python library for making HTTP requests)

## Installation

Download the latest version from GitHub to /usr/local/bin/:

```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/multappliednetworks/api-examples/master/enable-disable-leg/update-leg.py -O update-leg.py
sudo chmod +x update-leg.py
```
Install the Requests Python library:

```
sudo pip install --upgrade requests
```

## Usage

update-leg.py is configured with a few environment variables.

```
export BA_HOST='bondingadmin.example.com'
export BA_USER='you@example.com'
export BA_PASSWD='correct horse battery stable'
```

If your server doesn't have a properly signed SSL certificate, also do:
```
export BA_VERIFY_SSL=False
```

Then run the script with the bond ID, leg ID, and link mode as arguments:

```
/path/to/update-leg.py <bond-id> <leg-id> offline|idle|active
```

For example, with the script in /usr/local/bin/update-leg.py, a bond with ID 1, leg with ID 2, and target link mode of active, do:

```
/usr/local/bin/update-leg.py 1 2 active
```

If the request is successful, there will be no output, but it will write a short message to the syslog. If the request is unsuccessful, it will print an error message and exit with return value 1.


## Scheduling

You might want to run this command on a schedule. One way to do this is with [cron](http://man7.org/linux/man-pages/man5/crontab.5.html). This example cron file enables a leg at 22:00 and disables it at 06:00 every day:

```
BA_HOST=bondingadmin.example.com
BA_USER=you@example.com
BA_PASSWD='correct horse battery stable'
0 22 * * * nobody /usr/local/bin/update-leg.py 1 2 active
0 6  * * * nobody /usr/local/bin/update-leg.py 1 2 idle
```

(Remember to add BA_VERIFY_SSL=False if you don't have a properly signed SSL certificate.)

On Debian-based systems, putting this file at /etc/cron.d/update-leg would run the two commands as the "nobody" user. Error messages would be forwarded to the mailbox of the "nobody" user. Since it contains a username and password, you should ensure it's not world-readable:

```
sudo chmod 640 /etc/cron.d/update-leg
```

When running on a schedule, we recommend using a dedicated Bonded Internet user with a minimum level of privileges. This will reduce the risk to your server should the credentials be lost somehow.

