#!/bin/bash

if [ "x$1" == "x" ]
then
    exit 1
fi

dir=$1

while [ "$dir" != "/" ]
do
    chmod +x $dir
    dir=`dirname $dir`
done
