#!/bin/sh
# start_mqtt_connect.sh
#
# a simple script to connect to the MQTT source connect node and
# POST a JSON file with config properties for the Confluent MQTT source connector

hostname=$(cat hosts.yml| yq e '.kafka_connect_mqtt.hosts' - | sed s'/.$//')

echo "hostname is " && echo $hostname
echo "Making Connection to MQTT Server"
curl $hostname:8083/connectors -X POST -H "Content-Type: application/json" -d @mqtt_config.json


