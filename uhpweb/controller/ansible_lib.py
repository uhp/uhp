# -*- coding: UTF-8 -*- 

import ansible
import ansible.inventory
import ansible.playbook
from ansible.runner import Runner
from ansible.utils import template
import json

def connect_host(hosts,user,port,passwd,sudopasswd):
    #安装python-simplejson
    g_inv = ansible.inventory.Inventory(hosts)
    results = Runner(
         inventory=g_inv,
         module_name='raw', 
         module_args="yum -y install python-simplejson",
         pattern="all",
         sudo=True,
         remote_user=user,
         remote_port=port,
         remote_pass=passwd,
         sudo_pass=sudopasswd
    ).run()
    #由于，上个模式肯定运行失败，所以再次运行setup任务
    results = Runner(
         inventory=g_inv,
         module_name='setup', 
         module_args=" ",
         pattern="all",
         sudo=True,
         remote_user=user,
         remote_port=port,
         remote_pass=passwd,
         sudo_pass=sudopasswd
    ).run()

    ret={}
    if results is None:
       for host in hosts:
           ret[host]=(False,"No hosts found",{})
       return ret

    for host in hosts:
        ret[host]=(False,"unknow error",{})

    for (host, result) in results['contacted'].items():
        if not 'failed' in result:
            ret[host]=(True,"",get_info_from_result(result['ansible_facts']) )
        else:
            ret[host]=(False,result['msg'],{})
            print result
            
            
    for (host, result) in results['dark'].items():
        ret[host]=(False,result['msg'],{})

    return ret

def get_info_from_result(facts):
    cpu=("%d*%d*%dcore") % ( facts['ansible_processor_cores'],facts['ansible_processor_count'], facts['ansible_processor_threads_per_core'])
    ips=[]
    for interface in facts['ansible_interfaces']:
        face = 'ansible_'+interface;
        if facts.has_key(face) and facts[face].has_key("ipv4"):
            ip=facts[face]["ipv4"]["address"]
            if ip != "127.0.0.1" :
                ips.append(ip)
    mem=str(round( float(facts['ansible_memtotal_mb'])/1024 , 1 )) +"G"
    disks={}
    for mount in facts['ansible_mounts']:
        size_total=mount['size_total']
        type=size_to_type(size_total)
        if type != "" :
            if disks.has_key(type):
                disks[type]=disks[type]+1
            else:
                disks[type]=1
    diskstr=",".join( [ k+"*"+str(v) for (k,v) in disks.items() ] )
    return {"ip": ",".join(ips),"cpu":cpu,"mem":mem,"disk":diskstr,"rack":"default"}


def size_to_type(size):
    _1G=1024*1024*1024
    _50G=50*_1G
    _1T=1024*_1G
    if size < _50G :
        return "";
    elif size < _1T :
        return str(int(size/_1G))+"G";
    else:
        return str(int(size/_1T))+"T";

    
if __name__ == '__main__':
    print connect_host(["hadoop2","hadoop3"],"hadoop","9922","just4test","just4test")
