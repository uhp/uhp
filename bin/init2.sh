#!/bin/bash
set -e

if [ "$UHP_HOME" == "" ] ; then 
    DIR=$(cd $(dirname "$0");cd ..; pwd)
    echo "export UHP_HOME=$DIR" >> ~/.bash_profile
    echo "export ANSIBLE_CONFIG=\$HUP_HOME/conf/ansible.cfg" >> ~/.bash_profile
    echo "export PATH=\$UHP_HOME/bin:\$PATH" >> ~/.bash_profile
    export UHP_HOME=$DIR
fi

cd $UHP_HOME
chmod a+x bin/*.sh

export VIRTUAL_ENV="$UHP_HOME/vpy" 

#python lib/virtualenv-*.py --no-site-packages $VIRTUAL_ENV
#echo "export PATH=$VIRTUAL_ENV/bin:\$PATH" >> ~/.bash_profile
#export PATH=$VIRTUAL_ENV/bin:$PATH

sudo yum install -y make python2-devel mysql-devel

PIP="$VIRTUAL_ENV/bin/pip"

coms=("snakemq"
    "sqlalchemy"
    "tornado"    
    "threadpool"
    "callbacks"
    "pyyaml"
    "python-daemon"
    "mysql-python"
    "ansible"
    "lockfile")

for com in ${coms[@]}; do
    echo "--------$com--------"
    $PIP install $com
done 

exit 0
sudo yum install -y python-pip rpm-build make python2-devel mysql-devel
sudo pip-python install -U pip
sudo yum install -y ansible
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

chmod +x $UHP_HOME/inventor/mysqlinventory.py 

