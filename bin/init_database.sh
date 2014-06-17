#!/bin/bash

action=$1

if [ "$action" == "create" ] 
then
    cd $UHP_HOME/uhpcommon ; ./database.py create_db
elif [ "$action" == "drop" ] 
then
    cd $UHP_HOME/uhpcommon ; ./database.py drop_db
elif [ "$action" == "init" ] 
then
    cd $UHP_HOME/uhpcommon ; ./database.py init
    cd $UHP_HOME/conf/ansible_var/ ; ./import_db_conf.py all
else
    echo "init_database.py [action] "
    echo "                 create: create all db table"
    echo "                 init: import all default value"
    echo "                 drop: drop all data"  
fi


