import re
import json
from redis.sentinel import Sentinel
import redis
import subprocess


def connect_redis():
    return Sentinel([('127.0.0.1', 26379), 
                        ('127.0.0.1', 26380), 
                        ('127.0.0.1', 26381)], 
                        password="Abc@12314455", 
                        sentinel_kwargs={"password":"Abc@12314455"})

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
    docker_network = json.loads(subprocess.Popen('docker network inspect dcb-20231026_app-tier', stdout=subprocess.PIPE).stdout.read())
    containers = docker_network[0]["Containers"]
    return containers
 
def get_container_info(container_name):
    
    command = 'docker inspect {}'.format(container_name)
    container_info = json.loads(subprocess.Popen(command, stdout=subprocess.PIPE).stdout.read())
    host_port = container_info[0]["NetworkSettings"]["Ports"]
    for key, value in host_port.items():
        regex = r"^\d+(\/tcp|udp)$"
        if re.match(regex, key):
            port = value[0]['HostPort']
    return port

def get_ip(test_str):
    regex = r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
    matches = re.match(regex, test_str)
    return matches.group()

def redis_write_to_master(host, port):
    redis_client = redis.StrictRedis(
                host=host,
                port=port,
                password= "Abc@12314455") 
    return redis_client.set('foo', 'bar')

def test_replication_sync(host, port):
    redis_client = redis.StrictRedis(
                host=host,
                port=port,
                password= "Abc@12314455") 
    return redis_client.get('foo')

if __name__ == "__main__":
    sentinel = connect_redis()
    containers = get_redis_sentinel_info()
    master_host, _ = get_redis_master_info(sentinel)
    for _, container in containers.items():
        if master_host == get_ip(container["IPv4Address"]):
            current_master_port = get_container_info(container["Name"])
            print("Current Master with IP {} - HostPort {} - ContainerName {}".format(master_host, current_master_port, container["Name"]))
    # if redis_write_to_master("127.0.0.1", current_master_port): print("Success")
    try:
        slaves, _ = get_redis_slave_info(sentinel)
        for slave in slaves:
            for _, container in containers.items():
                if slave[0] == get_ip(container["IPv4Address"]):
                    current_slave_port = get_container_info(container["Name"])
                    print("Current Slave with IP {} - HostPort {} - ContainerName {}".format(slave[0], current_slave_port, container["Name"]))
    except:
        for _, container in containers.items():
            if master_host != get_ip(container["IPv4Address"]) and "sentinel" not in container["Name"]:
                current_slave_port = get_container_info(container["Name"])
                print("Current Slave with IP {} - HostPort {} - ContainerName {}".format(get_ip(container["IPv4Address"]), current_slave_port, container["Name"]))
                # test_replication_sync("127.0.0.1", current_slave_port)
