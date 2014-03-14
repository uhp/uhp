#!/bin/bash

srcdir=$1
dirname=`basename $1`
tarname=$2

cd ${srcdir}
tar -zcvf $tarname .

rm /tmp/$tarname -rf
mv $tarname  /tmp

