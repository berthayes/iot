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
0. CLI and Tools -> CLI Tools
    - Click Create API & Secret
      - Give the key a description
      - Make sure "show API keys" is checked (default)
      - Copy the provided configuration and save it to a file named ```config.properties``` in this directory.



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
        ```
        mosquitto_sub -h broker.hivemq.com -t 'HOSTNAME/#' -p 1883 -v
        ```
        - where ```HOSTNAME``` is e.g. the output of /bin/hostname

0. Create a connect config file for the MQTT connector
  - ```python3 create_mqtt_config.py```
  - This creates a file aclled ```mqtt_config.json```
  - This file is configured with the .properties files downloaded from Confluent Cloud.
0. Create the ```mqtt-connect``` topic in Confluent Cloud
  - In Confluent Cloud, go to Topics and click "Add a topic"
  - Create a new topic named mqtt-connect
  
  OR

  - In Confluent Cloud, go to CLI and Tools -> CCloud and CLI.
  - Follow steps 1 - 6 and create a topic called mqtt-connect
  ```
  ccloud kafka topic create mqtt-connect
  ```

0. Start the MQTT source connector
  - ```./start_mqtt_connect.sh```
    - This POSTs the ```mqtt_config.json``` file to the Connect node

## Transforming Metrics Data for Prometheus with ksqlDB
The ```cpu2mqtt.py``` sample script generates JSON objects that look like this:
```JSON
{
  "timestamp": 1617853878.558468,
  "user": 1.6,
  "nice": 0,
  "idle": 97.7,
  "system": 0.7
}
```
For a Prometheus gauge-style metric, we need to supply a record that looks like this:
```JSON
{
  "name": "cpu-idle",
  "type": "gauge",
  "timestamp": 1617854808.747522,
  "dimensions": {
    "device": "hostname",
    "sensor": "psutil"
  },
  "values": {
    "cpu_percent_idle": 98.5
  }
}
```
This transformation can be applied to streaming data using ksqlDB.

0. Create a new topic in Confluent Cloud
  - This topic will hold a single record, which will include field/value pairs for your Prometheus Metric.

  ```
  ccloud kafka topic create cpu_percent_idle
  ```
0. Create a producer.properties file
  - Go to Confluent Cloud -> Select your environment and cluster 
  - 
0. Populate this with a single record using the kafka-console-producer
  - Replace ```PRODUCER_BOOTSTRAP_SERVERS``` with the output from:
  ```
  cat my-connect-distributed.properties | grep producer\.bootstrap\.servers | awk -F= {'print $2'}
  ```
```
/opt/confluent/bin/kafka-console-producer --broker-list PRODUCER_BOOTSTRAP_SERVERS \
--producer.config config.properties \
--topic cpu_percent_idle \
--property "parse.key=true" \
--property "key.separator=:"
```
 - Enter this at the > prompt where ```HOSTNAME``` is your hostname (e.g. the output from /bin/hostname)
 ```
HOSTNAME/cpu_stats:{"name":"cpu_idle_percent","type":"gauge","device":"HOSTNAME","sensor":"psutil"}
```

Hit ctrl-c after that line of input has been accepted.

0. Create a ksqlDB application
  - In Confluent Cloud, go to ksqlDB and click "Add an Application"
  - Once the Application is created, open it and select "Editor"
  - Create a Stream from the mqtt data.  Set ```auto.offset.reset``` to ```Latest```
  ```SQL
  CREATE STREAM cpu_stream (
timestamp BIGINT,
device VARCHAR KEY,
user DOUBLE,
nice DOUBLE,
idle DOUBLE,
system DOUBLE
) WITH (KAFKA_TOPIC='mqtt-connect', VALUE_FORMAT='JSON');
```

- Set ```auto.offset.reset``` to ```Earliest```
- Create a table from the single event added using the Kafka console producer:
```SQL
CREATE TABLE cpu_idle_table (
name VARCHAR,
type VARCHAR,
device VARCHAR PRIMARY KEY,
sensor VARCHAR
) WITH (KAFKA_TOPIC='cpu_percent_idle', VALUE_FORMAT='JSON');
```
- Create a new Stream and a new topic that joins incoming MQTT data with the table containing Prometheus metrics fields.  Also, format the record for the Prometheus Sink Connector
```SQL
CREATE STREAM RICH_PROMETHEUS_CPU
WITH (KAFKA_TOPIC='rich_prometheus_cpu', VALUE_FORMAT='AVRO')
AS
SELECT
t.name AS "name",
t.type AS "type",
s.timestamp AS "timestamp",
s.DEVICE AS DEVICEID,
STRUCT(
"deviceid" := s.DEVICE,
"sensor" := t.SENSOR) AS "dimensions",
STRUCT("cpu_percent_idle" := CAST(s.idle AS DOUBLE)) AS "values"
FROM CPU_STREAM s
INNER JOIN CPU_IDLE_TABLE t on t.DEVICE = s.DEVICE
PARTITION BY s.DEVICE
EMIT CHANGES;
```
- Verify that events are being created and formatted correctly in the new topic:
```
/opt/confluent/bin/kafka-console-consumer --bootstrap-server CONSUMER_BOOTSTRAP_SERVER --consumer.config config.properties --topic rich_prometheus_cpu
```
