# Generating sample IoT data

If you don't have a streaming source for IoT data, the attached scripts can help.
## CTA_bustracker.py
- Make sure you have an API key from CTA!  See the "How to get an API key" section of the [Bus Tracker API Overview](https://www.transitchicago.com/developers/bustracker/).

This script uses your API key and polls the CTA Bus Tracker API every 30 seconds for details on 10 different routes; this data is then parsed out by Vehicle ID. The results are JSON objects that look like this:

```json
{
  "vid": "1742",
  "tmstmp": "20210604 12:55:50",
  "lat": "41.89198067847719",
  "lon": "-87.63119506835938",
  "hdg": "187",
  "pid": 3936,
  "rt": "22",
  "des": "Harrison",
  "pdist": 50514,
  "dly": false,
  "tatripid": "203968",
  "tablockid": "N22 -593",
  "zone": ""
}
```

Each JSON object is sent to the Confluent REST Proxy and ultimately to Confluent Cloud, using the ```vid``` value (Vehicle ID) as the key for each record.

Using ksqlDB, this data can be parsed and formatted as AVRO.  This creates a new topic which can be sent downstream to a Postgres server, which can then feed a Grafana Dashboard.

First, create a Stream from this topic:

```sql
CREATE STREAM bus_stream (
vid INT,
tmstmp VARCHAR,
lat DOUBLE(17,15),
lon DOUBLE(17,15),
hdg VARCHAR,
pid INT,
rt VARCHAR,
des VARCHAR,
pdist INT,
dly BOOLEAN,
tatripid VARCHAR,
tablockid VARCHAR,
zone VARCHAR)
WITH (KAFKA_TOPIC='bus-data', VALUE_FORMAT='JSON');
```

This ksql query takes the stream created above, and creates a new topic that is AVRO formatted and keyed by the ```VID``` value, which gets recreated as ```vehicleid``` in the value of each record:
```sql
CREATE STREAM bustracker_avro WITH (KAFKA_TOPIC='bustracker_avro', VALUE_FORMAT='AVRO') AS
SELECT *,
AS_VALUE(VID) AS vehicleid,
UNIX_TIMESTAMP(PARSE_TIMESTAMP(TMSTMP, 'yyyyMMdd HH:mm:ss', 'America/Chicago'))/1000 AS epoch
FROM BUS_STREAM PARTITION BY VID;
```

This new topic, ```bustracker_avro``` can sent to a Postgres database using Postgres Sink fully managed connector in Confluent Cloud.

Configure the Postgres Sink Connector with the following values, substituting the Postgres server listed in your hosts.yml file for connection.host.

    topics: bustracker_avro,
    input.data.format: AVRO,
    connector.class: PostgresSink,
    name: PostgresSinkConnector,
    connection.host: XXXXXXXXXXX.compute.amazonaws.com,
    connection.port: 5432,
    connection.user: postgres,
    db.name: bustracker,
    ssl.mode: prefer,
    insert.mode: UPSERT,
    db.timezone: America/Chicago,
    pk.mode: record_value,
    auto.create: true,
    auto.evolve: true,
    tasks.max: 1

## Mapping Bus Routes in Grafana

[Grafana.com](https://grafana.com) has a freemium model that allows developers and testers to run a few of their services for fee.

Go to Grafana.com and select "My Account" where you'll be redirected to the Grafana Cloud Portal.

Log In to Grafana.

Within Grafana, you can [add a data source](https://grafana.com/docs/grafana/next/datasources/add-a-data-source/?utm_source=grafana_gettingstarted)

If you don't already see it, search for Postgres and add it.  Once added, configure it accordingly, using the Postgres server hostname in your ```hosts.yml``` file:

![PostGres for Grafana](https://github.com/berthayes/iot/blob/main/images/grafana_postgres.png)

After you've tested and saved the data source, you can  query it to power a Grafana dashboard showing a single Vehicle's movement on a map using the [TrackMap panel](https://grafana.com/grafana/plugins/pr0ps-trackmap-panel/) 

![Mapping Bus 1510](https://github.com/berthayes/iot/blob/main/images/mapping_bus1510.png)

Or make a more traditional graph showing the number of delayed buses.

![Delayed Buses](https://github.com/berthayes/iot/blob/main/images/delayed_buses.png)