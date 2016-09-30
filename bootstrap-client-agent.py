#!/usr/bin/env python
import os
import sys
import paramiko
import argparse
import re
import getpass

"""
Configure argument parsing
"""
parser = argparse.ArgumentParser(description='Bootstrap a client agent \
                                for Red Hat Storage Console 2.0')

parser.add_argument("--type",
                    dest="type",
                    action="store",
                    choices=['mon', 'osd', 'rgw'],
                    required=True,
                    help='Define the type of client agent to bootstrap.  Valid \
                    options are mon, osd or rgw.')
parser.add_argument("--host",
                    dest="host",
                    required=True,
                    help='Define a host or list of comma-delimited hosts to \
                    bootstrap.')
parser.add_argument("--server",
                    dest="server",
                    required=True,
                    help='The target FQDN of a Red Hat Storage Console 2.0 \
                    server that clients will be connecting too')
args = parser.parse_args()

""" Provide parser validation """
def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

"""
Build a list of hosts
"""
# If only one host is given don't run the for loop
try:
    host_list = set(args.host.split(","))
    for each in host_list:
        if is_valid_hostname(each) == False:
            print "Error: The provided host: {0} does not appear to be a valid FQDN or IP address.".format(each)
            sys.exit(1)
except AttributeError:
    host_list = args.host
    if is_valid_hostname(host_list) == False:
        print "Error: The provided host: {0} does not appear to be a valid FQDN or IP address.".format(host_list)
        sys.exit(1)

# Run host check on the server seperately:
server = args.server
if is_valid_hostname(server) == False:
    print "Error: The provided server: {0} does not appear to be a valid FQDN or IP address.".format(server)
    sys.exit(1)

"""
Bootstrap prereqs
"""
# The only difference between the types is the repo subscription that is ran
# depending on the type installed
# Issue the correct subscription-manager repos --enable command for each type
if args.type == 'mon':
    repo_type = 'mon'
if args.type == 'osd':
    repo_type = 'osd'
if args.type == 'rgw':
    repo_type = 'tools'

rootPassword = getpass.getpass('Enter the root password for the host(s): ')
reposHosts = "subscription-manager repos --disable=* ; subscription-manager repos --enable=rhel-7-server-rhceph-2-{0}-rpms --enable=rhel-7-server-rhscon-2-agent-rpms --enable=rhel-7-server-rhscon-2-installer-rpms --enable=rhel-7-server-rpms".format(repo_type)
for each in host_list:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(each,
                username="root",
                password=rootPassword,
                look_for_keys=False
                )
stdin, stdout, stderr = ssh.exec_command(reposHosts)
# Wait for the subscription-manager commands to run
exit_status = stdout.channel.recv_exit_status()
if exit_status == 0:
    print "Subscribed host {0} to valid repositories".format(each)
    pass
else:
    print "Error subscribing host {0} to agent repositories. {1}".format(each, exit_status)
    client.close()
    sys.exit(1)

"""
Bootstrap client agent(s)
"""
print "Beginning bootstrapping process...  Updating each client with yum, starting ntpd and running setup agent.  This may take a few moments to complete..."
bootstrapCommand = 'yum update -y ; systemctl start ntpd ; curl {0}:8181/setup/agent | bash'.format(server)
stdin, stdout, stderr = ssh.exec_command(bootstrapCommand)
exit_status = stdout.channel.recv_exit_status()
if exit_status == 0:
    print(
"""The client agent has been installed and configured but may take a few moments
to appear in the Red Hat Storage Console web interface"""
    )
    pass
else:
    print "Error during bootstrap of host {0}. {1}".format(each, exit_status)
    client.close()
    sys.exit(1)
