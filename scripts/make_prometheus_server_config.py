# make_prometheus_server_config.py
#
# a simple script to read the hosts.yml file, pull out the
# Prometheus sink connector hostname and use it to replace
# a placeholder in a template file.

from ruamel.yaml import YAML
yaml = YAML()

hostinfo = open("hosts.yml", "r")
ymldata = yaml.load(hostinfo)

hostdict = ymldata['kafka_connect_prometheus']['hosts']
datadict = dict(hostdict)
host = list(datadict.keys())[0]
#print(host)
host_uri = host + ":8889"

prom = open("prom_server_default.yml", "r")
ymlprom = yaml.load(prom)

ymlprom['scrape_configs'][1]['static_configs'][0]['targets'][0] = host_uri

with open("prometheus.yml", "wt") as prom:
    yaml.dump(ymlprom, prom)

