import re
import subprocess

def get_cluster_nodes():
    nodes_info = subprocess.Popen('docker container ls -a', stdout=subprocess.PIPE).stdout.read()
    cluster_nodes_info = nodes_info.decode('utf-8').split("\n")[1:]
    return cluster_nodes_info

def get_nodes_id_name(info):
    if len(info.split("   ")) < 9:
        if "redis-node" in info.split("   ")[6]:
            return info.split("   ")[0], info.split("   ")[6]
        
    elif len(info.split("   ")) > 9:
        if "redis-node" in info.split("   ")[9]:
            return info.split("   ")[0], info.split("   ")[9]

def test_is_cluster_initiated(info):
    is_OK = True
    node_ids = ""
    for i in info:
        try:
            node_id, _ = get_nodes_id_name(i)
            cluster_sate = subprocess.Popen("docker exec -it {} redis-cli cluster info ".format(node_id), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            cluster_sate_output = cluster_sate.stdout.read().decode('utf-8').split("\n")[0]
            cluster_sate_err = cluster_sate.stderr.read().decode('utf-8').split("\n")[0]
            if "paused" in cluster_sate_err:
                is_OK = False
                node_ids += node_id
                
            pass
            if cluster_sate_output and "ok" not in cluster_sate_output:
                return "Cluster not initiated"
        except:
            pass
    if is_OK: return "Cluster initiated"
    if not is_OK: return "Cluster initiated but node {} was paused".format(node_ids)


def get_cluster_info(node_id):
    cluster_info = subprocess.Popen('docker exec -it {} redis-cli cluster nodes'.format(node_id), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    cluster_info_output = cluster_info.stdout.read().decode('utf-8').split("\n")
    cluster_info_err = cluster_info.stderr.read().decode('utf-8').split("\n")[0]
    return cluster_info_output, cluster_info_err

def node_detail(detail):
    d = detail.split(" ")
    if "slave" in d[2]:
        cluster_node_id = d[0]
        cluster_node_master = d[3]
        regex = r"((\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}):.+"
        matches = re.match(regex, d[1])
        ip = matches.group(1)
    else:
        cluster_node_id = d[0]
        cluster_node_master = d[3]
        regex = r"((\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}):.+"
        matches = re.match(regex, d[1])
        ip = matches.group(1)   
    return ip, cluster_node_id, cluster_node_master


def get_ip_role_nodes(details):
    try:
        for detail in details:
            if "myself" in detail:
                ip, cluster_node_id, cluster_node_master = node_detail(detail)
            if "fail" in detail:
                fail_ip, fail_cluster_node_id, _ = node_detail(detail)
                if fail_ip not in fail_ips and fail_cluster_node_id not in fail_cluster_nodes_id:
                    fail_ips.append(fail_ip)
                    fail_cluster_nodes_id.append(fail_cluster_node_id)
        return ip, cluster_node_id, cluster_node_master, fail_ips, fail_cluster_nodes_id
    except Exception as e:
        print(str(e))
        pass
    
def list_all_node_status(info):
    print("----------------Node Running----------------")
    for i in info:
        if len(i.split("   ")) > 1:
            node_id, _ = get_nodes_id_name(i)
            details, err = get_cluster_info(node_id)
            if not err:
                ip, cluster_node_id, cluster_node_master, fail_ips, fail_cluster_nodes_id = get_ip_role_nodes(details)
                print("Container ID: {} Node IP: {} Node ID: {} Master of Node: {}".format(node_id, ip, cluster_node_id, cluster_node_master))
    print("----------------Node Down----------------")
    for i in range(len(fail_ips)):
        print("Node IP: {} Node ID: {}".format(fail_ips[i], fail_cluster_nodes_id[i]))

if __name__ == "__main__":
    info = get_cluster_nodes()
    # print(test_is_cluster_initiated(info))
    fail_ips = []
    fail_cluster_nodes_id = []
    list_all_node_status(info)
