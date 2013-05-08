#!/usr/bin/env python

import sys
import logging
import argparse
import os
from os.path import expanduser

import pyrax
import pyrax.exceptions as exc
import exceptions

import functions
from functions import CloudServers
from functions import Status 

# Set loglevel
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

## Demo Preferences
# Instance name prefix 
prefix = "chefdemo"

# Image: Ubuntu 12.04 LTS image
image_id = "e4dbdba7-b2a4-4ee5-8e8f-4595b6d694ce"

# Flavor type
flavor_id = "2" # Name: 512MB Standard Instance, ID: 2, RAM: 512, Disk: 20, VCPUs: 1

# Number of servers to create
count = 2 

# Read in SSH Key
ssh_public_key_path = expanduser("~/.ssh/id_rsa.pub")
f = open(ssh_public_key_path)
ssh_public_key = f.read()

# Read in install script
#script = expanduser("~/install-script.sh")
#s = open(script)
#install_script = s.read()

# Setup files to copy into instance
#files={'/root/.ssh/authorized_keys': ssh_public_key, '/root/install-script.sh': install_script}
files={'/root/.ssh/authorized_keys': ssh_public_key}
logging.debug("Files: %s", (files))

# Launch server
myserver=CloudServers(prefix, image_id, flavor_id, count, files=files)
myserver.create_server()
