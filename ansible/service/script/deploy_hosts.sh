#!/bin/bash

#提供给web调用
#接收参数 host(要更新的机器) auto_add(要添加的host对)
#配合ansible/service/deploy_hosts.yml 和 ansible/service/replace_file.sh 使用
#本脚本直接调用ansible-playbook ansible/service/deploy_hosts.yml

host=$1
auto_add=$2

cd $UHP_HOME/ansible/service/
ansible-playbook -i $UHP_HOME/inventor/mysqlinventory.py deploy_hosts.yml -e "{\"WANT_HOST\":\"$host\",\"AUTO_ADD\":\"$auto_add\"}"
