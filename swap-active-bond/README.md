# Highly Available Bonders
This document describes how to set up a pair of highly-available bonders using keepalived/VRRP and a script that moves IP addresses between bonds using the management server API. It works by sharing common IPs between a master bonder and a backup bonder; the backup bonder takes over the IP addresses when it sees the master fail, and the master takes the IP back when it recovers.

When TCP proxy is enabled, all TCP sessions using the ports defined in the TCP proxy ports field will be interrupted when the active bonder changes. Applications will need to restart their sessions after the active bonder is changed.

##### Requirements
Two bonders with Bonded Internet >= 2016.1. Also note that while this is expected to work on Debian 7 ("Wheezy") bonders, the following documentation is intended for Debian 8 ("Jessie") bonders.

##### User and group setup (optional)
This part is optional but strongly recommended. Create a new permissions group with permission to view and change routing objects. Then make a new user account whose only group is the dedicated group you just created. This user will only have permission to view and change routing objects. Additionally, you can create this group within a child space, not the root space, to restrict the user to only making changes to routing objects on bonds within the child space or children of that space.

If you don't create a dedicated group and user account, you can use your own user account, but you'll have to put your password in the clear in a file on the bonders.

## Setup

##### Bonds
Create two bonds: one master and one backup. Each bond can have its own aggregator, bond settings, and legs, although in practice those settings will probably be the same. The bonders can share the same Internet lines for each of their legs.

##### Routing objects
On each bond, create one or more connected IPs, routes, or CPE NAT IPs. These are the IPs that will float between the master and backup devices depending on which one is active. On the master bond, these IPs should be enabled, and on the backup bond, they should be disabled.

Next, create a private IP used to communicate between the bonders themselves. These IPs must be different IPs in the same subnet; it can be a small /30 subnet. These can be on the same interface as one of the floating IPs, or they can be on a dedicated interface or VLAN.

###### Example connected IP configuration
* Master bond:
    * `203.0.113.1/30` enabled _(a connected IP that will move between bonders)_
    * `192.168.66.1/30` enabled _(the private IP for communication with the backup bonder)_
* Backup bond:
    * `203.0.113.1/30` **disabled**
    * `192.168.66.2/30` enabled

##### Image the bonders
Provision the master and backup bonders using the normal procedure.

##### Configure bonders as a HA pair
This section describes how to set up keepalived and a Python script that uses the management server API to take over the shared connected IP, route, or CPE NAT IP when a device becomes active. Perform each step on both the master and backup bonders.

Connect the interfaces having the private IPs on each bond to the same Ethernet network, and the interfaces having the public IPs on each bond to the same network. This could be a single network with all the IPs, or it could be two separate networks or VLANs- one network for the floating IPs, and one network for the bonders to monitor each other using the private IPs.

**Warning:** The interfaces having the private IPs on each bond must not be connected directly. If they are, the interface will lose carrier when either bonder goes down and keepalived will assume it to be a fault and not fail over the routing objects.

##### Install and configure swap-active-bond script
This script is available on GitHub. On each bonder, download it to `/usr/local/bin`:

    wget https://raw.githubusercontent.com/multappliednetworks/api-examples/master/swap-active-bond/swap-active-bond.py -O /usr/local/bin/swap-active-bond.py
    chmod +x /usr/local/bin/swap-active-bond.py

This script reads its configuration from `/etc/bonding/swap-active-bond.conf`, so download an example configuration file on the master bonder:

    wget -nc https://raw.githubusercontent.com/multappliednetworks/api-examples/master/swap-active-bond/swap-active-bond.example.conf -O /etc/bonding/swap-active-bond.conf

To download the file even if the destination file `/etc/bonding/swap-active-bond.conf` already exists, remove the `-nc` argument.

Edit the file `/etc/bonding/swap-active-bond.conf` and set these values:

In the `[bondingadmin]` section:
* `host`: Domain name of the management server.
* `user`: Username or email address of the user account used to update the routing objects.
* `passwd`: Password of the user account
* `verify_ssl`: Whether or not to verify that the management server's SSL certificate is signed by a recognized authority ("true"), or to not verify that ("false"). Defaults to true. If your management server uses a self-signed certificate, you must set this to false.
* `timeout`: Number of seconds to wait for each request to the management server- default 10.
* `attempts`: Number of requests to make to the management server until one succeeds- default 3.
* `attempt_delay`: Number of seconds to wait between requests to the management server- default 5.

In the `[bond]` section:
* `master_bond_id`: The ID of the master bond as reported in the management server.
* `master_connected_ip_ids`: The IDs of the floating connected IPs on the master bond. If multiple IPs are required, separate using commas, eg: 1, 2, 3
* `master_route_ids`: The IDs of the floating routes on the master bond. If multiple routes are required, separate using commas, eg: 1, 2, 3
* `master_cpe_nat_ip_ids`: The IDs of the floating CPE NAT IPs on the master bond. If multiple CPE NAT IPs are required, separate using commas, eg: 1, 2, 3
* `backup_bond_id`: The ID of the backup bond.
* `backup_connected_ip_ids`: The IDs of the floating connected IPs on the backup bond. If multiple IPs are required, separate using commas, eg: 3, 4, 5
* `backup_route_ids`: The IDs of the floating routes on the backup bond. If multiple routes are required, separate using commas, eg: 1, 2, 3
* `backup_cpe_nat_ip_ids`: The IDs of the floating CPE NAT IPs on the backup bond. If multiple CPE NAT IPs are required, separate using commas, eg: 1, 2, 3

__Note:__ To omit any of connected IPs, routes, or CPE NAT IPs, simply omit values for their respective options in `/etc/bonding/swap-active-bond.conf`. For example, if only connected IPs apply for your bond:

    [bond]
    master_bond_id = 1
    master_connected_ip_ids = 1,2
    backup_bond_id= 3
    backup_connected_ip_ids= 4,5

Once you've completed the configuration, copy the file to the same location on the backup bonder.

To test the script, simply run it on the command line:

    /usr/local/bin/swap-active-bond.py VI_1 1 MASTER 10

The arguments are specified by keepalived- the first two are unused, the third should always be MASTER when testing, and the final argument should be 10 to test as on the master bonder, and 9 to test as on the backup bonder.

An error message will be printed if the script encounters any problems, such as an incorrect username or password, DNS failure, permission problems, or inability to locate the bonds or routing objects via their IDs.

When run as the master, the script will disable the routing objects on the backup bond and enable the one on the master bond.

When run as the backup, it will disable the routing objects on the master bond and enable the one on the backup bond.

##### Install and configure keepalived on the bonders
On each bonder, install keepalived:

    apt-get install keepalived -y

On the master, download an example keepalived config file to `/etc/keepalived/keepalived.conf`:

    wget -nc https://raw.githubusercontent.com/multappliednetworks/api-examples/master/swap-active-bond/keepalived.example.conf -O /etc/keepalived/keepalived.conf

Edit the file `/etc/keepalived/keepalived.conf` and change these values:
* `interface`: The interface on which the private IP lives on that bonder (it does not need to be the same for the master and backup)
* `state`: MASTER on the master bonder, BACKUP on the backup bonder
* `priority`: Priority on the master must be 10, and priority on the backup must between 1 and 9. 10 is used as a special number in the `swap-active-bond.py` script to determine if it's running on the master or backup bonder.
* `unicast_src_ip`: Private IP on the bonder
* `unicast_peer`: Private IP on the other bonder (note that this is within squiggly brackets)
* `auth_pass`: Password for simple authentication between the nodes

Once you've completed the configuration, copy the file to the same location on the backup bonder and change the appropriate values (`state`, `priority`, `unicast_src_ip`, `unicast_peer`, and possibly `interface`).

Enable and start keepalived on each bonder:

    systemctl enable keepalived.service
    systemctl start keepalived.service

You can monitor the state of the system using this command, which displays logs from the keepalived service:

    journalctl -u keepalived.service -f

## Testing
Now you're ready to test. Follow these steps to test high availability:
* Reboot each bonder to ensure their configurations are up-to-date and states are in sync.
* Connect a router to the Ethernet network used for the floating IP. Configure the router with a static IP in the subnet of the public IP and ping the public IP, which should be live on the master bonder. The ping should succeed. Alternatively, you can ping a host on the Internet to verify the full routing path.
* Reboot the master bonder. This simulates a hardware failure. The ping will fail for a short period of time until the ARP cache expires on the router. On a Linux router, this is about 30-40 seconds. When the cache expires, the ping will succeed, this time pinging the backup bonder. When the master reboots and comes back online, it will take over from the backup after another short outage.
* On the master bonder, run this command:

        systemctl stop bonding

* This simulates a software failure. Note that if you run this command in an SSH session using an IP managed by bonding, the IP will be removed and you'll either need to log in via the serial console or monitor/keyboard to restart bonding, or will need to restart the bonder to restart bonding.
* The ping should halt after bonding stops, then resume when the router's ARP cache is cleared and it can access the backup bonder.

#### See also
Keepalived tutorials and documentation:
* https://www.digitalocean.com/community/tutorials/how-to-set-up-highly-available-web-servers-with-keepalived-and-floating-ips-on-ubuntu-14-04
* https://tobrunet.ch/2013/07/keepalived-check-and-notify-scripts/
* http://www.keepalived.org/pdf/UserGuide.pdf
* http://linux.die.net/man/5/keepalived.conf
* https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/Load_Balancer_Administration/ch-lvs-overview-VSA.html#s1-lvs-keepalived-VSA
