import requests
import json

# Uses the CTA Bus Tracker API (documentation available here):
# https://www.transitchicago.com/assets/1/6/cta_Bus_Tracker_API_Developer_Guide_and_Documentation_20160929.pdf

# Given a list of Route Designators ('rt' below), return Vehicle IDs
# JSON response will be most recent status for each vehicle

# Take that JSON response and send it Confluent Kafka REST Proxy

# TODO: wrap this in a loop so it runs every minute or so (check AUP)

# Confluent REST Proxy values
rest_proxy_host = "ec2-52-14-116-180.us-east-2.compute.amazonaws.com"
topic = "bustest"
rest_headers = {'Content-Type': 'application/vnd.kafka.json.v2+json', 'Accept': 'application/vnd.kafka.v2+json'}
rest_url = "http://" + rest_proxy_host + ":8082/topics/" + topic

# CTA Bus Tracker API values
api_key = 'HL76TdXUt6YZGmTKSziz3qXyT'
getvehicles_url = 'http://ctabustracker.com/bustime/api/v2/getvehicles'

# Format the API request and parse the response
vehicle_params = {'key': api_key, 'format': 'json', 'rt': 'X9,11,12,J14,15,18,19,20,21,22', 'tmres': 's'}
r_vehicles = requests.get(getvehicles_url, params=vehicle_params)
# each JSON object is the latest stats for each vehicle ID (bus).
response_dict = r_vehicles.json()
vehicle_dict = response_dict['bustime-response']
list_of_vids = vehicle_dict['vehicle']


for vid in list_of_vids:
    # each vid is a dict
    list_of_records = []
    kafka_record = {}
    kafka_record['value'] = vid
    # use the vehicle ID - vid as the key for each record
    kafka_record['key'] = vid["vid"]
    list_of_records.append(kafka_record)
    send_data = {}
    send_data['records'] = list_of_records
    send_json = json.dumps(send_data)
    print(send_json)
    # POST to the REST API
    kpost = requests.post(rest_url, headers=rest_headers, data=send_json)
    print(kpost.text)
#    time.sleep(10)