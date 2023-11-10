import argparse
from doctest import master
from email import parser
import re
import json
import sys
from redis.sentinel import Sentinel
import redis
import subprocess


def connect_redis():
    try:
        return Sentinel([('127.0.0.1', 26379), 
                            ('127.0.0.1', 26380), 
                            ('127.0.0.1', 26381)], 
                            password="Abc@12314455", 
                            sentinel_kwargs={"password":"Abc@12314455"})
    except:
        return("Try again")

def get_redis_master_info(sentinel):
    try:
        host, port = sentinel.discover_master("master-sentinel")
        return host, port
    except:
        pass

def get_redis_slave_info(sentinel):
    try:
        host, port = sentinel.discover_slaves("master-sentinel")
        return host, port
    except:
        pass

def get_redis_sentinel_info():
    docker_network = json.loads(subprocess.Popen('docker network inspect dcb-20231026_redis-sentinel', stdout=subprocess.PIPE).stdout.read())
    containers = docker_network[0]["Containers"]
    return containers
 
def get_container_info(container_name):
    try:
        command = 'docker inspect {}'.format(container_name)
        container_info = json.loads(subprocess.Popen(command, stdout=subprocess.PIPE).stdout.read())
        host_port = container_info[0]["NetworkSettings"]["Ports"]
        for key, value in host_port.items():
            regex = r"^\d+(\/tcp|udp)$"
            if re.match(regex, key):
                port = value[0]['HostPort']
        return port
    except:
        pass

def get_ip(test_str):
    regex = r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
    matches = re.match(regex, test_str)
    return matches.group()

def redis_write_to_master(host, port, key, value):
    try:
        redis_client = redis.StrictRedis(
                    host=host,
                    port=port,
                    password= "Abc@12314455") 
        print("Writing to Redis Key: {} Value: {}".format(key, value))
        return redis_client.set(key, value)
    except:
        return "Can not connect to Master Host"
def test_replication_sync(host, port, key):
    try:
        
        redis_client = redis.StrictRedis(
                    host=host,
                    port=port,
                    password= "Abc@12314455") 
        return redis_client.get(key)
    except:
        return "Can not connect to Slave Host"

def redis_master_infor(sentinel, containers):
    master_host, _ = get_redis_master_info(sentinel)
    try:
        for _, container in containers.items():
            if master_host == get_ip(container["IPv4Address"]):
                # current_master_port = get_container_info(container["Name"])
                print("Current Master with IP {} - ContainerName {}".format(master_host, container["Name"]))
    except:
        pass

def redis_slave_infor(sentinel, containers):
    master_host, _ = get_redis_master_info(sentinel)
    try:
        slaves, _ = get_redis_slave_info(sentinel)
        for slave in slaves:
            for _, container in containers.items():
                if slave[0] == get_ip(container["IPv4Address"]):
                    # current_slave_port = get_container_info(container["Name"])
                    print("Current Slave with IP {} - ContainerName {}".format(slave[0], container["Name"]))
    except:
        for _, container in containers.items():
            if master_host != get_ip(container["IPv4Address"]) and "sentinel" not in container["Name"]:
                # current_slave_port = get_container_info(container["Name"])
                print("Current Slave with IP {} - ContainerName {}".format(get_ip(container["IPv4Address"]), container["Name"]))

if __name__ == "__main__":
    sentinel = connect_redis()
    containers = get_redis_sentinel_info()
    # master = sentinel.master_for('master-sentinel', password="Abc@12314455")
    # master.set('foo', 'bar')
    # slave = sentinel.slave_for('master-sentinel', password="Abc@12314455")
    # slave.get('foo')
    parser = argparse.ArgumentParser(description='Option')
    subparsers = parser.add_subparsers(title='Subcommand', description='Description')
    subparsers.add_parser('master')
    subparsers.add_parser('replica')
    parser_get=subparsers.add_parser('get')
    parser_get.add_argument('--key')
    parser_get.add_argument('--port')
    parser_set=subparsers.add_parser('set')
    parser_set.add_argument('--key')
    parser_set.add_argument('--value')
    parser_set.add_argument('--port')
    try:
        args = parser.parse_args()
        port = args.port
        key = args.key
        value = args.value
    except:
        pass
    if sys.argv[1] == "set":
        if redis_write_to_master("127.0.0.1", port, key, value): print("Success")
    if sys.argv[1] == "get":
        if test_replication_sync("127.0.0.1", port, key): print(test_replication_sync("127.0.0.1", port, key).decode("utf-8"))        
    if sys.argv[1] == "master":
        redis_master_infor(sentinel, containers)
    if sys.argv[1] == "replica":
        redis_slave_infor(sentinel, containers)   
