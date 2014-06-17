#!/bin/bash
set -e

DIR=$(cd $(dirname "$0"); cd ..; pwd)

if [ "$UHP_HOME" == "" ] ; then 
    echo "export UHP_HOME=$DIR" >> ~/.bash_profile
    echo "export ANSIBLE_CONFIG=\$HUP_HOME/conf/ansible.cfg" >> ~/.bash_profile
    echo "export PATH=\$UHP_HOME/bin:\$PATH" >> ~/.bash_profile
    export UHP_HOME=$DIR
fi

cd $DIR

chmod a+x bin/*.sh

export VIRTUAL_ENV="$DIR/vpy" 

sudo rm -rf $VIRTUAL_ENV

coms=(
    "redhat-lsb"
    "cairo-devel"
    "pango-devel"
    "libxml2-devel"
    "libxslt-devel"
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
    echo "###############################################"
done 

echo 
echo "Install vpy ..."
echo 

python lib/virtualenv-*.py --no-site-packages $VIRTUAL_ENV
echo "export PATH=$VIRTUAL_ENV/bin:\$PATH" >> ~/.bash_profile
export PATH=$VIRTUAL_ENV/bin:$PATH

echo 
echo "pip install ..."
echo 

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
    "simpleparse"
    "lxml"
    )

for com in ${coms[@]}; do
    echo "###############################################"
    echo "# install: $com"
    echo "###############################################"
    sudo $PIP install $com
    echo "###############################################"
done 

SITE_P=$(ls -d $VIRTUAL_ENV/lib/python*/site-packages/)
( cd $SITE_P && sudo mv -f rrdtoolmodule.so rrdtoolmodule.so.bk && cp $DIR/lib/rrdtoolmodule.so ./rrdtoolmodule.so )
#检查ansible安装成功
RE=`ansible --version|grep ansible|wc -l`
if [ "$RE" == "0" ] ; then
    echo "ansible not found" ;
    exit 1;
fi

mkdir -p $UHP_HOME/logs/web
mkdir -p $UHP_HOME/logs/monitor
mkdir -p $UHP_HOME/logs/worker

mkdir -p $UHP_HOME/db

chmod +x $UHP_HOME/inventor/mysqlinventory.py 
echo "All is OK!"
