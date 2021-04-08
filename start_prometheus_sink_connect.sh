#!/bin/sh
# start_prometheus_sink_connect.sh
#
# a simple script to read the hosts.yml file, extract the Prometheus
# sink connect hostname, connect to it and POST a JSON config file
# to start the Prometheus sink connector


hostname=$(cat hosts.yml| yq e '.kafka_connect_prometheus.hosts' - | sed s'/.$//')

echo "hostname is " && echo $hostname
echo "Making Connection to Prometheus Connect Sink node"
curl $hostname:8083/connectors -X POST -H "Content-Type: application/json" -d @prom_config.json


