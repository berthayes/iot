# cpu2mqtt - a simple script to read cpu metrics using
# the psutil library, then send them to an mqtt broker

# TODO: pull some of these configs from a config file

import paho.mqtt.client as paho
#import paho.mqtt.publish as publish
import socket
import psutil
import time
import json

hostname = socket.gethostname()

def on_connect(client, userdata, flags, rc):
    print("CONNACK received with code ")
    print(rc)

def on_publish(client, userdata, mid):
    print("mid: " + str(mid))

client = paho.Client(client_id=hostname, clean_session=True, userdata=None, protocol=paho.MQTTv31)
client.on_connect = on_connect
client.connect("broker.hivemq.com", 1883)


client.on_publish = on_publish
client.loop_start()

while True:
    # cpu_times_percent is the percent
    #(rc, mid) = client.publish(“encyclopedia / temperature”, str(temperature), qos = 1)
    cpu_times_percent = psutil.cpu_times_percent(interval=1, percpu=False)
    cpu_stats = {}
    cpu_stats["timestamp"] = time.time()
    cpu_stats["user"] = cpu_times_percent.user
    cpu_stats["nice"] = cpu_times_percent.nice
    cpu_stats["idle"] = cpu_times_percent.idle
    cpu_stats["system"] = cpu_times_percent.system
    print(cpu_stats)
    payload = json.dumps(cpu_stats)
    print(payload)
    mqtt_topic = hostname + "/cpu_stats"
    print(mqtt_topic)
    (rc, mid) = client.publish(mqtt_topic, payload=payload)
    time.sleep(30)