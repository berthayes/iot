# Transforming Metrics Data for Prometheus with ksqlDB
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

1. Create a new topic in Confluent Cloud
  - This topic will hold a single record, which will include field/value pairs for your Prometheus Metric.

  ```
  ccloud kafka topic create cpu_percent_idle
  ```
1. Create a producer.properties file
  - Go to Confluent Cloud -> Select your environment and cluster 
1. Populate this with a single record using the kafka-console-producer
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

1. Create a ksqlDB application
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
