# IoT & Confluent Cloud Quickstart 
A turnkey environment for sending IoT data to Confluent Cloud.
- [Overview](https://github.com/berthayes/iot/#Overview)
- [Configuring Your Environment](https://github.com/berthayes/iot/#Configuring-Your-Environment)
- [Create Confluent Cloud Configs](https://github.com/berthayes/iot/#Create-Confluent-Cloud-Configs)
- [Create Configured Containers](https://github.com/berthayes/iot/#Create-Configured-Containers)
- [Metrics Data with MQTT](https://github.com/berthayes/iot/#metrics-data-with-mqtt)
- [Transforming Metrics Data for Prometheus with ksqlDB](https://github.com/berthayes/iot/blob/main/ksql-for-prometheus.md)
- [Try Confluent Cloud for Free](https://www.confluent.io/confluent-cloud/tryfree)
- [Kafka Tutorials & Examples](https://developer.confluent.io/#kafka-tutorials-and-examples)

## Overview
By default, this code is designed to create and configure two separate AWS EC2 instances as:
  - [Confluent REST Proxy](https://docs.confluent.io/platform/current/kafka-rest/index.html)
  - [Kafka Connect Node](https://docs.confluent.io/platform/current/connect/index.html)
    - [Confluent MQTT Connector (Source & Sink)](https://www.confluent.io/hub/confluentinc/kafka-connect-mqtt) is installed.
      - Requires an existing MQTT Broker (e.g. [hivemq.com](https://www.hivemq.com))

Once created, these hosts will be automatically configured for your cluster in Confluent Cloud.  This automation is achieved with an Ansible playbook using the scripts included in this repository.  

Optionally, two additional EC2 instances can be created and configured as:
  - [Kafka Connect Node](https://docs.confluent.io/platform/current/connect/index.html)
    - [Prometheus Sink Connector](https://www.confluent.io/hub/confluentinc/kafka-connect-prometheus-metrics) is installed.
  - [Promethus Server](https://prometheus.io/)
  
Data from the Prometheus server can optionally be sent to Grafana.com which has a free tier and includes native Prometheus integration.

![Cloud IoT Architecture](https://github.com/berthayes/iot/blob/main/images/iot_arch.png)

## Configuring Your Environment
### Prerequisites and assumptions
The python scripts that talk to AWS use the boto3 library, which by default looks for your AWS credentials and confg in ```~/.aws/credentials``` and ```~/.aws.config``` . If you don't have these files already, see [this page](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) for information on how to get them.
### Editing yak_shaving.conf

The ```yak_shaving.conf``` file is used by multiple scripts to create the example environment in AWS.

- The ```[aws_common]``` section requires details unique to your own AWS environment.

1. Create a Security Group in the EC2 Management Console that allows inbound access from your network to the following ports:
    - TCP 22 - SSH - Used by Ansible for deployment and shell access for user troubleshooting
    - TCP 8083 - Used for the REST API for Kafka Connect
    - TCP 8082 - Used for the Confluent REST Proxy
    - TCP 8089 - Used for the Prometheus Sink Connector and the Prometheus Server (optional)
1. The AMI used is Ubuntu 18.04 LTS, but Ubuntu 20.04 will work and Debian 10 might even work too.
1. The ```owner_name```, ```your_pem```, ```your_email```, and ```cluster_name``` fields are all used by the ```create_aws_instances.py``` script to create and correctly identify the EC2 instances.  Note that ```your_pem``` is not the path to your EC2 SSH key, but rather the name of the Key pair name of an instance in the EC2 console.  ```path_to_pem``` is the file path to your AWS SSH key - this is used by Ansible when configuring hosts.



## Create Confluent Cloud Configs
1. Go to your Confluent Cloud Cluster
    CLI and Tools -> Confluent Platform Components -> Rest Proxy [Connect]
    - Create Kafka cluster API key & secret
    - Create Schema Registry API key & secret
      - make sure "show API keys" is checked (default)
    - Click Copy, and paste the contents into a file and save it as ```ccloud-kafka-rest.properties``` in the samedirectory as these scripts.
    - Do the same for the optional stuff, adding it to the end of ```ccloud-kafka-rest.properties```
1. CLI and Tools -> Kafka Connect
    - Click Distributed
    - Create Kafka cluster API key & secret
    - Create Schema Registry API key & secret
    - Click the checkbox for "Requires Enterprise License"
      - Make sure "show API keys" is checked (default)
    - Click "Generate Config"
    - Click Copy, and paste the contents into a file named ```my-connect-distributed.properties```
1. CLI and Tools -> CLI Tools
    - Click Create API & Secret
      - Give the key a description
      - Make sure "show API keys" is checked (default)
      - Copy the provided configuration and save it to a file named ```config.properties``` in this directory.

## Create Configured Containers
1. Spin up EC2 instances
    - ```python3 create_aws_instances.py```
1. Give a minute for the instances to start up.  Pet the dog/cat.

1. Run basic host update stuff with Ansible & configure all nodes for their roles
    - ```python3 create_hosts_dot_yaml.py```
    - ```ansible -i hosts.yml -m ping all```
    - ```ansible-playbook -i hosts.yml all.yml```


## Metrics data with MQTT
The Confluent MQTT Source connector assumes that you already have an MQTT broker deployed.
 - The default config in ```yak_shaving.conf``` is to use a free demo MQTT broker brovided by Hive MQ
  - Edit ```[mqtt-connect]``` section to change the ```mqtt_server```
  
### Starting the MQTT Source Connector
1. Create the ```mqtt-connect``` topic in Confluent Cloud
    - In Confluent Cloud, go to Topics and click "Add a topic"
    - Create a new topic named mqtt-connect
1. Create a connect config file for the MQTT connector
    - ```python3 create_mqtt_config.py```
    - This creates a file called ```mqtt_config.json```
    - This file is configured with the .properties files downloaded from Confluent Cloud.
1. Start the MQTT source connector
    - ```./start_mqtt_connect.sh```
      - This POSTs the ```mqtt_config.json``` file to the Connect node
### Generating sample data with cpu2mqtt.py  script.

The included ```cpu2mqtt.py``` python script uses the psutil and paho.mqtt python libraries to read CPU stats and send them to an MQTT broker
  - ```python3 cpu2mqtt.py```
  - The script uses your system hostname (e.g. the output from /bin/hostname) as the MQTT topic name.
  - You can verify that data is being sent to the HiveMQ broker by going to http://www.hivemq.com/demos/websocket-client/
        or running
  ```
  mosquitto_sub -h broker.hivemq.com -t 'HOSTNAME/#' -p 1883 -v
  ```
  where ```HOSTNAME``` is e.g. the output of /bin/hostname

## Transforming IOT Data for Prometheus with ksqlDB
This portion of the readme is moved [here](https://github.com/berthayes/iot/blob/main/ksql-for-prometheus.md)
