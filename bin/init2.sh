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

sudo rm -rf $VIRTUAL_ENV

coms=(
    "redhat-lsb"
    "cairo-devel"
    "pango-devel"
    "libxml2-devel"
    "rrdtool-devel"
    "make"
    "python2-devel"
    "mysql-devel"
    )

for com in ${coms[@]}; do
    echo "###############################################"
    echo "# install: $com"
    echo "###############################################"
    sudo yum install -y $com
done 

python lib/virtualenv-*.py --no-site-packages $VIRTUAL_ENV
echo "export PATH=$VIRTUAL_ENV/bin:\$PATH" >> ~/.bash_profile
export PATH=$VIRTUAL_ENV/bin:$PATH

PIP="$VIRTUAL_ENV/bin/pip"

coms=(
    "snakemq"
    "sqlalchemy"
    "tornado"    
    "threadpool"
    "callbacks"
    "pyyaml"
    "python-daemon"
    "mysql-python"
    "ansible"
    "python-rrdtool"
    "lockfile"
    )

for com in ${coms[@]}; do
    echo "###############################################"
    echo "# install: $com"
    echo "###############################################"
    sudo $PIP install $com
done 

rm -f $UHP_HOME/vpy/lib/python2.*/site-packages/rrdtoolmodule.so
cp $UHP_HOME/lib/rrdtoolmodule.so ./vpy/lib/python2.*/site-packages/rrdtoolmodule.so

#sudo yum install -y python-pip rpm-build make python2-devel mysql-devel
#sudo pip-python install -U pip
#sudo yum install -y ansible
#check ansible 
#检查ansible安装成功
RE=`ansible --version|grep ansible|wc -l`
if [ "$RE" == "0" ] ; then
    echo "ansible not found" ;
    exit 1;
fi

#ansible all -m ping
mkdir -p $UHP_HOME/logs/web
mkdir -p $UHP_HOME/logs/monitor
mkdir -p $UHP_HOME/logs/worker

mkdir -p $UHP_HOME/db

chmod +x $UHP_HOME/inventor/mysqlinventory.py 
echo "All is OK!"
