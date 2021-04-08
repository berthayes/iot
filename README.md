# IoT & DoT Demo & Quickstart 
A turnkey environment for sending IoT data to Confluent Cloud.

This code is designed to spin up and configure EC2 instances as:
  - REST Proxy
  - MQTT Connect Source
  - Prometheus Connect Sink
  - Prometheus Server

Once created, these hosts will send/receive data to/from Confluent Cloud.  Data from the Prometheus server can optionally be sent to Grafana.com which has a free tier which includes native Prometheus integration.

0. Go to your Confluent Cloud Cluster
    CLI and Tools -> Confluent Platform Components -> Rest Proxy [Connect]
    - Create Kafka cluster API key & secret
      - Give it a description
    - Create Schema Registry API key & secret
      - Give it a description
      - make sure "show API keys" is checked (default)
    - Click Copy, and paste the contents into a file and save it as ```ccloud-kafka-rest.properties``` in the samedirectory as these scripts.
    - Do the same for the optional stuff, adding it to the end of ```ccloud-kafka-rest.properties```
0. CLI and Tools -> Kafka Connect
    - Click Distributed
    - Create Kafka cluster API key & secret
      - Give it a description
    - Create Schema Registry API key & secret
      - Give it a description
    - Click the checkbox for "Requires Enterprise License"
      - Make sure "show API keys" is checked (default)
    - Click Copy, and paste the contents into a file named ```my-connect-distributed.properties```

0. Spin up EC2 instances
    - ```python3 create_aws_instances.py```
0. Give a minute for the instances to spin up.  Pet the dog/cat.

0. Run basic host update stuff with Ansible & configure all nodes for their roles
    - ```python3 create_hosts_dot_yaml.py```
    - ```ansible -i hosts.yml -m ping all```
    - ```ansible-playbook -i hosts.yml all.yml```

This ```all.yml``` playbook also runs specific playbook for different hosts

  - Create docker-compose.yml for MQTT Connect
    - copy ```my-connect-distributed.properties```
    - run ```create_connect_docker_compose_dot_yaml.py```
    - run docker-compose up to start connector

  - Create docker-compose.yml for Prometheus Connect
    - copy ```my-connect-distributed.properties```
    - run ```create_connect_docker_compose_dot_yaml.py```
    - runs docker-compose up to start connector
    - copy docker-compose.yml for REST Proxy
    - copy ```ccloud-kafka-rest.properties``` 

  - Create config file for Prometheus Server
    - Start Prometheus Server which scrapes kafka connect node for metrics


## Metrics data with MQTT

### Generating sample data with attached script.
 - The default config in ```yak_shaving.conf``` is to use a free demo MQTT broker brovided by Hive MQ
  - Edit ```[mqtt-connect]``` section to change the ```mqtt_server```
  - The included ```cpu2mqtt.py``` python script uses the psutil and paho.mqtt python libraries to read CPU stats and send them to an MQTT broker
    - ```python3 cpu2mqtt.py```
    - The script uses your system hostname (e.g. the output from /bin/hostname) as the MQTT topic name.
    - You can verify that data is being sent to the HiveMQ broker by going to
        http://www.hivemq.com/demos/websocket-client/
        or running
        ```mosquitto_sub -h broker.hivemq.com -t 'HOSTNAME/#' -p 1883 -v```
        - where ```HOSTNAME``` is e.g. the output of /bin/hostname

0. Create a connect config file for the MQTT connector
  - ```python3 create_mqtt_config.py```
  - This creates a file aclled ```mqtt_config.json```
  - This file is configured with the .properties files downloaded from Confluent Cloud.
0. Start the MQTT source connector
  - ```./start_mqtt_connect.sh```
    - This POSTs the ```mqtt_config.json``` file to the Connect node



