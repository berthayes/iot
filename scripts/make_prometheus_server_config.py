# make_prometheus_server_config.py
#
# a simple script to read the hosts.yml file, pull out the
# Prometheus sink connector hostname and use it to replace
# a placeholder in a template file.

from ruamel.yaml import YAML
yaml = YAML()

ansible_inventory = '/home/ubuntu/iot/hosts.yml'
# TODO: make this come from a command line arg
hostinfo = open(ansible_inventory, "r")
ymldata = yaml.load(hostinfo)

hostdict = ymldata['kafka_connect_prometheus']['hosts']
datadict = dict(hostdict)
host = list(datadict.keys())[0]
#print(host)
host_uri = host + ":8889"

prom_server_default = '/home/ubuntu/iot/scripts/prom_server_default.yml'
# TODO: make this come from a command line arg
prom = open(prom_server_default, "r")
ymlprom = yaml.load(prom)

ymlprom['scrape_configs'][1]['static_configs'][0]['targets'][0] = host_uri

with open("prometheus.yml", "wt") as prom:
    yaml.dump(ymlprom, prom)

