#!/usr/bin/env python

import sys
import logging
import argparse
import time
import os
from os.path import expanduser

import pyrax
import pyrax.exceptions as exc
import exceptions

class Setup():
    def __init__(self):
        # Authenticate to London Rackspace Cloud
        conf = os.path.expanduser("~/creds")
        pyrax.set_credential_file(conf, "LON")

        # Set pointers to cloud services
        self.cs = pyrax.cloudservers
        self.dns = pyrax.cloud_dns
        self.clb = pyrax.cloud_loadbalancers

class Status(Setup):
    def __init__(self, server_id):
        Setup.__init__(self)

        self.server_id = server_id

    def get_status(self):
        logging.debug("Checking status of server:")
        logging.debug("server_id: %s", (self.server_id))

        server = self.cs.servers.get(self.server_id)
        logging.debug ("server.status: %s", (server.status))
        return server.status


class CloudServers(Setup):
    def __init__(self, prefix, image_id, flavor_id, count, files):
        
        # Import creds and pointers from Setup class
        Setup.__init__(self)

        # Setup servers list to use later
        self.servers = []

        # Pull vars into class
        self.prefix = prefix
        self.image_id = image_id
        self.flavor_id = flavor_id
        self.count = count
        self.files = files
    
    def random_name(self, prefix):
        # Generate a random server name with a predefined prefix
        self.server_name = self.prefix + "-" + pyrax.utils.random_name(8, True)
        logging.debug("Random server_name: %s", (self.server_name))

        return self.server_name
    
    def create_server(self):
        logging.debug("Starting server creation loop")
        logging.debug("image_id: %s", (self.image_id))
        logging.debug("flavor_id: %s", (self.flavor_id))

        for i in xrange(0, self.count):
            logging.info("Creating server...")
            
            self.random_name(self.prefix)
    
            server = self.cs.servers.create(self.server_name, self.image_id, self.flavor_id, files=self.files)
            self.servers.append(server)
            logging.info("Name: %s\n ID: %s\n Status: %s\n Password: %s\n Networks: %s\n" % (server.name, server.id, server.status, server.adminPass, server.networks))

    def get_publicip(server_id):
        logging.debug("Getting IPv4 Address of server:")
        logging.debug("server_id: %s", (server_id))

        server = cs.servers.get(server_id)
        logging.debug("Public IP: %s\n" % (server.accessIPv4))

        return server.accessIPv4

    def get_servers(self):
        """ Return list of servers launched by create_server, much like cs.servers.list() """
        logging.debug("Populating list of servers")

        servers=[]

        for server in self.servers:
            logging.debug("Server ID: %s" % (server.id))
            servers.append(self.cs.servers.get(server.id))
        
        logging.debug("Servers %s" % (servers))

        # Return list of server objects 
        return servers

class Bootstrap(Setup):
    def ssh_bootstrap(server_ip):
        cmd = "bash -x /root/install-script.sh"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_ip, username='root')
        stdin, stdout, stderr = ssh.exec_command(cmd)
        ssh.close()

    def knife_bootstrap(server_id):
        server = cs.servers.get(server_id)
        roles = "apt,aliases,apache2,networking_basic,chef-demo"

        os.system("knife bootstrap --node-name %s --no-host-key-verify %s -r %s" % (server.name, server.accessIPv4, roles))

    def knife_remove(server_name):
        server = cs.servers.get(server_id)
        os.system("knife rackspace server delete -y %s" % (server.name))
        os.system("knife node delete -y %s" % (server.name))
        os.system("knife client delete -y %s" % (server.name))

class CloudDNS(Setup):
    def __init__(self, domain_name, domain_email, domain_ttl, domain_comment):
        Setup.__init__(self)

        self.domain_name = domain_name
        self.domain_email = domain_email
        self.domain_ttl = domain_ttl
        self.domain_comment = domain_comment

    def create_domain(self):
        try:
            logging.debug("Creating domain: %s" % (domain_name))
            dom = dns.create(name=self.domain_name, emailAddress=self.domain_email, ttl=self.domain_ttl, comment=self.domain_comment)
        except exc.DomainCreationFailed:
            logging.info("DomainCreationFailed!")
            logging.info("Trying to get existing domain record...")
        try:
            dom = dns.find(name=self.domain_name)
            logging.debug("Domain: %s" % (dom))
        except exc.NotFound:
            logging.info("Domain not found")
            pass

    def create_record(domain_name, fqdn_name, ip_addr):
        dom = dns.find(name=domain_name)
        a_record = {
                "type": "A",
                "name": fqdn_name,
                "data": ip_addr,
                "ttl": 6000,
                }

        recs = dom.add_records([a_record])

    def delete_domain(domain_name):
        dom = dns.find(name=domain_name)
        dom.delete()
