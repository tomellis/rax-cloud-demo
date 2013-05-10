#!/usr/bin/env python

import os
from os.path import expanduser
import sys
import pyrax

# Authenticate to London Rackspace Cloud
conf = os.path.expanduser("~/creds")
pyrax.set_credential_file(conf, "LON")

# Instance name prefix 
prefix = "chefdemo"

# Set pointers to cloud services
cs = pyrax.cloudservers
dns = pyrax.cloud_dns

def delete_server():
    servers = cs.servers.list()
    for server in servers:
        if prefix in server.name:
            print "Terminating Server: %s - %s  " % (server.name, server.id)
            knife_remove(server.name)
            server.delete()

def delete_domain():
    domains = dns.list()
    for domain in domains:
        if prefix in domain.name:
            print "Deleting domain: %s and all records " % (domain.name)
            domain.delete()

def knife_remove(server_name):
    os.system("knife rackspace server delete -y %s" % (server_name))
    os.system("knife node delete -y %s" % (server_name))
    os.system("knife client delete -y %s" % (server_name))
    
delete_domain()
delete_server()
