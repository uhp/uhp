#!/bin/bash
set -e

if [ "$UHP_HOME" == "" ] ; then 
    echo "UHP_HOME is not set; please insert export UHP_HOME=$HOME/uhp into your env" ;
    exit 1; 
fi

sudo yum install -y python-pip rpm-build make python2-devel mysql-devel
sudo pip-python install -U pip
sudo yum install -y ansible-1.4.3
sudo yum install -y rrdtool rrdtool-python
#check ansible 
#检查ansible安装成功
#RE=`ansible  --version|grep ansible|wc -l`
#if [ "$RE" == "0" ] ; then
#    echo "ansible not found" ;
#    exit 1;
#fi

#ansible all -m ping
mkdir -p $UHP_HOME/logs/web
mkdir -p $UHP_HOME/logs/monitor
mkdir -p $UHP_HOME/logs/worker

mkdir -p $UHP_HOME/db


sudo pip install ansible
sudo pip install snakemq
#sudo pip install mysql.connector
sudo pip install sqlalchemy
sudo pip install tornado
sudo pip install daemon
sudo pip install threadpool
sudo pip install callbacks
sudo pip install mysql-python
sudo pip install lockfile
sudo pip install python-daemon 
sudo pip install psutil

chmod +x $UHP_HOME/inventor/mysqlinventory.py 

