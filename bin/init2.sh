#!/bin/bash
set -e

DIR=$(cd $(dirname "$0"); cd ..; pwd)

if [ "$UHP_HOME" == "" ] ; then 
    echo "export UHP_HOME=$DIR" >> ~/.bash_profile
<<<<<<< HEAD
    #echo "export ANSIBLE_CONFIG=\$HUP_HOME/conf/ansible.cfg" >> ~/.bash_profile
=======
    echo "export ANSIBLE_CONFIG=\$UHP_HOME/conf/ansible.cfg" >> ~/.bash_profile
>>>>>>> c117605ad3e8dec9a381f120306b91596f0ab4b6
    echo "export PATH=\$UHP_HOME/bin:\$PATH" >> ~/.bash_profile
    export UHP_HOME=$DIR
fi

cd $DIR

rm -rf $HOME/.ansible.cfg
cp $DIR/conf/ansible.cfg $HOME/.ansible.cfg

chmod a+x bin/*.sh

export VIRTUAL_ENV="$DIR/vpy" 
VIRTUAL_ENV2="$UHP_HOME/vpy" 

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

#rh_ver=$(lsb_release -a |sed -n 4p|awk '{print $2}')
py_ver=$( python -V 2>&1|awk '{print $2}' )
if [ $py_ver >= "2.6.0" ]; then
    coms+=(
        "python2-devel"
    )
else
    coms+=(
        "python26"
        "python26-devel"
    )
fi

for com in ${coms[@]}; do
    echo "###############################################"
    echo "# install: $com"
    echo "###############################################"
    sudo yum install -y $com
    echo "###############################################"
done 

if [ $py_ver >= "2.6.0" ]; then
    ;
else
    sudo mv -f /usr/bin/python /usr/bin/python.bk
    sudo ln -s /usr/bin/python2.6 /usr/bin/python
fi


echo 
echo "Install vpy ..."
echo 

python lib/virtualenv-*.py --no-site-packages $VIRTUAL_ENV
echo "export PATH=$VIRTUAL_ENV2/bin:\$PATH" >> ~/.bash_profile
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

mkdir -p $DIR/logs/web
mkdir -p $DIR/logs/monitor
mkdir -p $DIR/logs/worker
mkdir -p $DIR/db

chmod +x $DIR/inventor/mysqlinventory.py 
echo "All is OK!"
