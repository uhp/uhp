#!/bin/bash

app=$1

cd $UHP_HOME/ansible/service/
ansible-playbook -i $UHP_HOME/inventor/mysqlinventory.py kill_app.yml -e "{\"APP\":\"$app\"}"

