# create_mqtt_config.py
#
# read a .properties file from Confluent Cloud and create a JSON
# config file to send to the Connect REST API to start a
# Confluent MQTT source connector

import tempfile
import json
from configparser import ConfigParser
import socket

connect_conf = "my-connect-distributed.properties"
mqtt_conf_template = "mqtt_config_template.json"
mqtt_generated_config = "mqtt_config.json"
yak_conf = "./yak_shaving.conf"

with tempfile.NamedTemporaryFile(delete=False, mode='wt') as t:
    t.write('[conf]')
    path = t.name
    #print(path)

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

mqtt_server = cfg.get('mqtt-connect', 'mqtt_server')
kafka_topic = cfg.get('mqtt-connect', 'kafka_topic')
mqtt_topic = socket.gethostname()
mqtt_topic = mqtt_topic + "/cpu_stats"
mqtt_server_uri = "tcp://" + mqtt_server + ":1883"

with open(mqtt_conf_template, 'r') as f:
    mqtt_dict = json.loads(f.read())


config_dict = mqtt_dict['config']
config_dict['value.converter.schema.registry.url'] = schema_url
config_dict['key.converter.schema.registry.url'] = schema_url
config_dict['value.converter.schema.registry.basic.auth.user.info'] = schema_creds
config_dict['mqtt.topics'] = mqtt_topic
config_dict['kafka.topic'] = kafka_topic
config_dict['mqtt.server.uri'] = mqtt_server_uri
config_dict['confluent.topic.bootstrap.servers'] = license_broker
config_dict['confluent.topic.sasl.jaas.config'] = api_key


#print(json.dumps(mqtt_dict))

with open(mqtt_generated_config, 'wt') as c:
    c.write(json.dumps(mqtt_dict, indent=4))
