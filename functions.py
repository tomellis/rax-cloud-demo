#!/usr/bin/env python

import logging
import os
import time
import pyrax
import pyrax.exceptions as exc


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
    """ Helper functions running directly against the public cloud """
    def __init__(self, server_id):
        Setup.__init__(self)

        self.server_id = server_id
        self.server = self.cs.servers.get(self.server_id)

    def get_status(self):
        logging.debug("Checking status of server_id: %s", (self.server_id))
        logging.debug("server.status: %s", (self.server.status))

        return self.server.status

    def get_publicip(self):
        logging.debug("Getting IPv4 Address of server_id: %s", (self.server_id))
        logging.debug("server.accessIPv4: %s\n" % (self.server.accessIPv4))

        return self.server.accessIPv4


class CloudServers(Setup):
    """ Launch CloudServers """
    def __init__(self, prefix, image_id, flavor_id, count, files, domain_name, domain_email, domain_ttl, domain_comment, rackconnect=False):

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
        self.domain_name = domain_name
        self.domain_email = domain_email
        self.domain_ttl = domain_ttl
        self.domain_comment = domain_comment
        self.rackconnect = rackconnect

    def random_name(self, prefix):
        # Generate a random server name with a predefined prefix
        self.server_name = self.prefix + "-" + pyrax.utils.random_name(8, True)
        logging.debug("Random server_name: %s", (self.server_name))

        return self.server_name

    def create_server(self):
        logging.debug("Starting server creation loop")
        logging.debug("image_id: %s", (self.image_id))
        logging.debug("flavor_id: %s", (self.flavor_id))

        # Debug only: Test class to avoid spawning servers when debugging
        #class Struct:
        #    def __init__(self, **entries):
        #        self.__dict__.update(entries)
        #s = {'name': "testserver", 'accessIPv4':"172.19.0.1", 'id':"1234", 'status':"ACTIVE", 'adminPass':"testing", 'networks':"none", 'metadata':
        #    {"rackconnect_automation_feature_configure_network_stack": "ENABLED", 
        #    "rackconnect_automation_feature_manage_software_firewall": "ENABLED", 
        #    "rackconnect_automation_feature_provison_public_ip": "ENABLED", 
        #    "rackconnect_automation_status": "DEPLOYING"} }
        #server = Struct(**s)

        for i in xrange(0, self.count):
            logging.info("Creating server...")

            self.random_name(self.prefix)

            server = self.cs.servers.create(self.server_name, self.image_id, self.flavor_id, files=self.files)
            # Append server details to our own server list
            self.servers.append(server)
            logging.debug("Name: %s\n ID: %s\n Status: %s\n Password: %s\n Networks: %s\n" % (server.name, server.id, server.status, server.adminPass, server.networks))
            logging.info("Building Server: %s - ID: %s\n" % (server.name, server.id))
            # Set up callback thread so that waiting for server to become active is non-blocking
            pyrax.utils.wait_until(server, "status", ["ACTIVE", "ERROR"], callback=self.bootstrap, interval=20, attempts=0, verbose=False)
            # Debug only:
            #self.bootstrap(server)

    def get_servers(self):
        """ Return list of servers launched by create_server, much like cs.servers.list() """
        logging.debug("Populating list of servers")

        servers = []

        for server in self.servers:
            logging.debug("Server ID: %s" % (server.id))
            servers.append(self.cs.servers.get(server.id))

        logging.debug("Get_servers: Servers %s" % (servers))

        # Return list of server objects
        return servers

    def rackconnect_status(self, server_id):
        if self.rackconnect is True:
            # If we are using rackconnect make sure we don't add the record until the IP has changed from public to rackconnectIP 
            rcs = self.cs.servers.get(server_id)
            print "DEBUG: ", rcs
            print rcs.metadata
            while rcs.metadata['rackconnect_automation_status'] == "DEPLOYING":
                logging.info("Waiting for RackConnect... Sleeping.")
                time.sleep(10)
                logging.debug("Name: %s\n ID: %s\n Public IP: %s\n RackConnectStatus: %s\n" % (server.name, server.id, server.accessIPv4, rcs.metadata['rackconnect_automation_status']))

    def create_domain(self):
        try:
            logging.debug("Creating domain: %s" % (self.domain_name))
            dom = self.dns.create(name=self.domain_name, emailAddress=self.domain_email, ttl=self.domain_ttl, comment=self.domain_comment)
        except exc.DomainCreationFailed:
            logging.info("DomainCreationFailed!")
            logging.info("Trying to get existing domain record...")
        try:
            dom = self.dns.find(name=self.domain_name)
            logging.debug("Domain: %s" % (dom))
        except exc.NotFound:
            logging.info("Domain not found")

    def create_record(self, server_name, ip_addr):
        logging.debug("Creating A record: %s - %s" % (server_name, ip_addr))
        try:
            dom = self.dns.find(name=self.domain_name)
        except exc.NotFound:
            logging.info("Can't find existing domain, record creation failed")

        a_record = {
            "type": "A",
            "name": server_name + "." + self.domain_name,
            "data": ip_addr,
            "ttl": 6000,
        }
        try:
            dom.add_records([a_record])
        except exc.DomainRecordAdditionFailed:
            logging.info("Failed to add dns record, may already exist!")

    def knife_bootstrap(server):
        roles = "apache2,chef-demo"
        os.system("knife bootstrap --node-name %s --no-host-key-verify %s -r %s" % (server.name, server.accessIPv4, roles))

    def bootstrap(self, server):
        logging.info("Server Built!\n Server Name: %s\n Server ID: %s\n Status: %s\n " % (server.name, server.id, server.status))
        self.create_domain()
        self.rackconnect_status(server.id)
        self.create_record(server.name, server.accessIPv4)


class CloudDNS(Setup):
    def __init__(self, domain_name, domain_email, domain_ttl, domain_comment):
        Setup.__init__(self)

        # DNS vars
        self.domain_name = domain_name
        self.domain_email = domain_email
        self.domain_ttl = domain_ttl
        self.domain_comment = domain_comment

    def create_domain(self):
        try:
            logging.debug("Creating domain: %s" % (self.domain_name))
            dom = self.dns.create(name=self.domain_name, emailAddress=self.domain_email, ttl=self.domain_ttl, comment=self.domain_comment)
        except exc.DomainCreationFailed:
            logging.info("DomainCreationFailed!")
            logging.info("Trying to get existing domain record...")
        try:
            dom = self.dns.find(name=self.domain_name)
            logging.debug("Domain: %s" % (dom))
        except exc.NotFound:
            logging.info("Domain not found")
            pass

    def create_record(self, domain_name, fqdn_name, ip_addr):
        try:
            dom = self.dns.find(name=self.domain_name)
        except exc.NotFound:
            logging.info("Can't find existing domain, record creation failed")

        a_record = {
            "type": "A",
            "name": fqdn_name,
            "data": ip_addr,
            "ttl": 6000,
        }

        try:
            dom.add_records([a_record])
        except exc.DomainRecordAdditionFailed:
            logging.info("Failed to add dns record, may already exist!")

    def delete_domain(self, domain_name):
        dom = self.dns.find(name=self.domain_name)
        dom.delete()
