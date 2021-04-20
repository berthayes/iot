#!/usr/local/bin/python3

# read a file from command line or a .properties file and
# turn it into a docker-compose.yml file
# or at least format the fields appropriately.

import os
import re
import ruamel.yaml
import requests

try:
    r = requests.get('http://169.254.169.254/latest/meta-data/public-hostname', timeout=1)
    advertised_hostname = r.text
except:
    advertised_hostname = '0.0.0.0'

file = '../ccloud-kafka-rest.properties'
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
                    dcfield = 'KAFKA_REST_' + ufield
                    value = fv.group(2)
                    environment[dcfield] = value
            environment['KAFKA_REST_LISTENERS'] = "http://0.0.0.0:8082"
        input_file.close()
    except:
        print("I am slain!")
        exit()
else:
    print(file + " does not exist")
    print("I am slain!")
    exit()


env = {}
env['environment'] = environment

yaml = {}
yaml['version'] = '2'

version = {}
services = {}
rest = {}
rest['image'] = 'confluentinc/cp-kafka-rest:6.1.1'
rest['hostname'] = 'rest-proxy'
rest['container_name'] = 'kafka-rest-proxy'
rest['ports'] = ["8082:8082"]
rest['environment'] = environment

yaml['version'] = '2'
yaml['services'] = services
services['rest-proxy'] = rest


docker_compose_file = ruamel.yaml.round_trip_dump(yaml, explicit_start=True)

with open('../rest-docker-compose.yml', 'wt') as dc:
    dc.write(str(docker_compose_file))
