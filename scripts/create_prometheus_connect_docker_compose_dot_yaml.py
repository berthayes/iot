#!/usr/local/bin/python3

# read a file from command line or a .properties file and
# turn it into a docker-compose.yml file
# or at least format the fields appropriately.

import os
import re
import ruamel.yaml
import requests
import secrets

try:
    r = requests.get('http://169.254.169.254/latest/meta-data/public-hostname', timeout=1)
    advertised_hostname = r.text
except:
    advertised_hostname = '0.0.0.0'

file = '../my-connect-distributed.properties'
# TODO: Make this not hard coded.

if os.path.exists(file):
    try:
        with open(file, 'rt') as input_file:
            environment = {}
            for line in input_file:
                if re.match(r'^\s+', line):
                    #print("leading whitespace")
                    continue
                elif re.match(r'\w+', line):
                    line = line.strip()
                    line = str(line)
                    # split line on = into field/value
                    fv = re.match(r'([^\=]*)=(.*)', line)
                    field = fv.group(1)
                    field_ = re.sub(r'\.', r'_', field)
                    ufield = field_.upper()
                    dcfield = 'CONNECT_' + ufield
                    value = fv.group(2)
                    #if re.match(r'^\d', value):
                    #    value = int(value)
                    environment[dcfield] = value
                    #print("environment[" + dcfield + "] = " + value)
            environment['CONNECT_REST_ADVERTISED_HOST_NAME'] = advertised_hostname
            prefix = secrets.token_urlsafe(4)
            environment['CONNECT_GROUP_ID'] = prefix + '-prometheus'
            environment['CONNECT_CONFIG_STORAGE_TOPIC'] = prefix + '-prometheus-storage'
            environment['CONNECT_STATUS_STORAGE_TOPIC'] = prefix + '-prometheus-status'
            environment['CONNECT_OFFSET_STORAGE_TOPIC'] = prefix + '-prometheus-offset'
            #print(environment)
        input_file.close()
    except:
        print("Can't do stuff here")
        exit()


env = {}
env['environment'] = environment

yaml = {}
yaml['version'] = '2'

version = {}
services = {}
connect = {}
connect['image'] = 'confluentinc/cp-server-connect:6.1.1'
connect['hostname'] = 'prometheus-connect'
connect['container_name'] = 'prometheus-connect'
connect['ports'] = ["8083:8083", "8889:8889"]
connect['environment'] = environment

yaml['version'] = '2'
yaml['services'] = services
services['connect'] = connect


docker_compose_file = ruamel.yaml.round_trip_dump(yaml, explicit_start=True)

forgive_me = '''    command:
      - bash
      - -c
      - |
        echo "Installing connector plugins"
        confluent-hub install --no-prompt confluentinc/kafka-connect-prometheus-metrics:latest
        echo "Launching Kafka Connect worker"
        /etc/confluent/docker/run'''

#print(forgive_me)
with open('docker-compose.yml', 'wt') as dc:
    dc.write(str(docker_compose_file))
    dc.write(forgive_me)
