# create_prometheus_sink_config.py
# read a .properties file saved from Confluent Cloud and create a JSON
# config file to POST to the Connect REST API to start the
# Confluent Prometheus sink connector

import tempfile
import json
from configparser import ConfigParser

host_uri = "http://0.0.0.0:8889/metrics"


connect_conf = "/home/ubuntu/iot/my-connect-distributed.properties"
prom_conf_template = "/home/ubuntu/iot/prometheus_config_template.json"
prom_generated_config = "/home/ubuntu/iot/prom_config.json"
yak_conf = "/home/ubuntu/iot/yak_shaving.conf"

with tempfile.NamedTemporaryFile(delete=False, mode='wt') as t:
    t.write('[conf]')
    path = t.name

    with open(connect_conf, 'r') as f:
        for line in f:
            t.write(line)


cfg = ConfigParser()
cfg.read(path)

schema_url = cfg.get('conf', 'value.converter.schema.registry.url')
schema_creds = cfg.get('conf', 'value.converter.schema.registry.basic.auth.user.info')
license_broker = cfg.get('conf', 'confluent.topic.bootstrap.servers')
api_key = cfg.get('conf', 'sasl.jaas.config')
#print(schema_url)

cfg = ConfigParser()
cfg.read(yak_conf)

#prom_server = cfg.get('kafka_connect_prometheus', 'prom_server')
kafka_topic = cfg.get('kafka_connect_prometheus', 'kafka_topic')

with open(prom_conf_template, 'r') as f:
    prom_dict = json.loads(f.read())


config_dict = prom_dict['config']
config_dict['value.converter.schema.registry.url'] = schema_url
config_dict['key.converter.schema.registry.url'] = schema_url
config_dict['value.converter.schema.registry.basic.auth.user.info'] = schema_creds
config_dict['topics'] = kafka_topic
config_dict['confluent.topic.bootstrap.servers'] = license_broker
config_dict['confluent.topic.sasl.jaas.config'] = api_key
config_dict['sasl.jaas.config'] = api_key
config_dict['reporter.bootstrap.servers'] = license_broker
config_dict['confluent.topic.bootstrap.servers'] = license_broker
config_dict['producer.bootstrap.servers'] = license_broker
config_dict['consumer.bootstrap.servers'] = license_broker
config_dict['consumer.sasl.jaas.config'] = api_key
config_dict['producer.sasl.jaas.config'] = api_key
config_dict['bootstrap.servers'] = license_broker
config_dict['prometheus.listener.url'] = host_uri


#print(json.dumps(prom_dict))

with open(prom_generated_config, 'wt') as c:
    c.write(json.dumps(prom_dict, indent=4))
