#!/usr/bin/env python

import sys
import logging
import argparse
import os
from os.path import expanduser

import pyrax
import pyrax.exceptions as exc
import exceptions

class CloudFunctions:
    def __init__(self, prefix, image_id, flavor_id, count, files):
        # Authenticate to London Rackspace Cloud
        conf = os.path.expanduser("~/creds")
        pyrax.set_credential_file(conf, "LON")

        # Set pointers to cloud services
        self.cs = pyrax.cloudservers
        self.dns = pyrax.cloud_dns
        self.clb = pyrax.cloud_loadbalancers

        # Pull vars into class
        self.prefix = prefix
        self.image_id = image_id
        self.flavor_id = flavor_id
        self.count = count
        self.files = files

    def create_server(self):
        logging.debug("Starting server creation loop")
        logging.debug("image_id: %s", (self.image_id))
        logging.debug("flavor_id: %s", (self.flavor_id))

        for i in xrange(0, self.count):
            logging.info("Creating server...")
    
            self.server_name = self.prefix + "-" + pyrax.utils.random_name(8, True)
            logging.debug("Random server_name: %s", (self.server_name))

            server = self.cs.servers.create(self.server_name, self.image_id, self.flavor_id, files=self.files)
            print "Name: ", server.name
            print "ID: ", server.id
            print "Status: ", server.status
            print "Password: ", server.adminPass
            print "Networks: ", server.networks

    def server_status(server_id):
        logging.debug("Checking status of server:")
        logging.debug("server_id: %s", (server_id))

        server = cs.servers.get(server_id)
        print server.status

    def get_publicip(server_id):
        logging.debug("Getting IPv4 Address of server:")
        logging.debug("server_id: %s", (server_id))

        server = cs.servers.get(server_id)
        print "Public IP: %s\n" % (server.accessIPv4)

    def ssh_bootstrap(server_ip):
        cmd = "bash -x /root/install-script.sh"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_ip, username='root')
        stdin, stdout, stderr = ssh.exec_command(cmd)
        #print stdout.readlines()
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

    def create_domain(domain_name, domain_email, domain_ttl, domain_comment):
        try:
            print "Creating domain: ", domain_name
            dom = dns.create(name=domain_name, emailAddress=domain_email, ttl=domain_ttl, comment=domain_comment)
        except exc.DomainCreationFailed:
            print "DomainCreationFailed!"
            print "Trying to get existing domain record..."
        try:
            dom = dns.find(name=domain_name)
            print dom
        except exc.NotFound:
            print "Domain not found"
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
