#!/bin/bash

if [ "$UHP_HOME" == "" ] ; then 
    echo "UHP_HOME is not set; please insert export UHP_HOME=$HOME/uhp into your env" ;
    exit 1; 
fi

cd $UHP_HOME
rm $UHP_HOME/build -rf
mkdir -p $UHP_HOME/build
svn export $UHP_HOME $UHP_HOME/build/uhp/
cd $UHP_HOME/build
tar -zcf uhp.tar.gz uhp
cd $UHP_HOME/build


