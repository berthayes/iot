# create_hosts_dot_yaml.py
#
# read a config file and connect to AWS via boto3 library
# find all running EC2 instances that match config specs
# and turn them into a hosts.yml file for ansible, etc.

import boto3
from configparser import ConfigParser
import ruamel.yaml

output_file = 'hosts.yml'

cfg = ConfigParser()
cfg.read('yak_shaving.conf')

pem = cfg.get('aws_common', 'your_pem')
path_to_pem = cfg.get('aws_common', 'path_to_pem')
cluster_name = cfg.get('aws_common', 'cluster_name')

ec2 = boto3.client('ec2')
node_filters = [
    {'Name': 'tag:cluster_name', 'Values': [cluster_name]},
    {'Name': 'key-name', 'Values': [pem]},
    {'Name': 'instance-state-name', 'Values': ['running']}
]

response = ec2.describe_instances(Filters=node_filters)
#print(response)

# response is a dictionary
# response['Reservations'] is a list
Reservations = response['Reservations']

# Reservations is a list of dictionaries.
# Each dictionary includes a list of Groups and a list of Instances

nodes_list = []
jobs_list = []
hosthash = {}

for res_dict in Reservations:
    instance_list = res_dict['Instances']
    for instance_dict in instance_list:
        try:
            instance_dict['PrivateIpAddress']
        except KeyError:
            private_ip = "NULL"
        else:
            private_ip = instance_dict['PrivateIpAddress']
        try:
            instance_dict['PrivateDnsName']
        except KeyError:
            private_dns = "NULL"
        else:
            private_dns = instance_dict['PrivateDnsName']
        try:
            instance_dict['PublicDnsName']
        except KeyError:
            public_dns = "NULL"
        else:
            public_dns = instance_dict['PublicDnsName']
        try:
            instance_dict['PublicIpAddress']
        except KeyError:
            public_ip = "NULL"
        else:
            public_ip = instance_dict['PublicIpAddress']
        tags = instance_dict['Tags']
        for tag_dict in tags:
            for key in tag_dict:
                if tag_dict.get(key) == 'Name':
                    ec2_name = tag_dict['Value']
                elif tag_dict.get(key) == 'node_job':
                    node_job = tag_dict['Value']
                elif tag_dict.get(key) == 'cluster_name':
                    cluster_name = tag_dict['Value']

    # Is host_info actually used anywhere?  Why am I creating it?
    host_info = {
        'ec2_name': ec2_name,
        'node_job': node_job,
        'cluster_name': cluster_name,
        'public_ip': public_ip,
        'private_ip': private_ip,
        'public_dns': public_dns,
        'private_dns': private_dns
        }

    hosthash[public_dns] = node_job

    jobs_list.append(node_job)
    nodes_list.append(public_dns)

# create a de-duplicated list of node jobs/roles
dedup = list(dict.fromkeys(jobs_list))

# create dictionary of 'all' common variables
all = {}
vars = {}
vars['vars'] = {
    'ansible_connection': 'ssh',
    'ansible_user': 'ubuntu',
    'ansible_become': 'true',
    'ansible_ssh_private_key_file': path_to_pem
}

all['all'] = vars

common_vars = ruamel.yaml.round_trip_dump(all)

with open(output_file, 'wt') as output:
    for role in dedup:
        hosts = {}
        for n in nodes_list:
            if hosthash[n] == role:
                hosts[n] = None

            mcgilla = {}
            mcgilla[role] = {'hosts': hosts}

        #print(mcgilla)
        nodes_yaml = ruamel.yaml.round_trip_dump(mcgilla)
        output.write(str(nodes_yaml))

    output.write(str(common_vars))
