#!/bin/bash

tarName=$1
dirName=$2
user=$3

rm $dirName/* -rf
tar -zxvf $tarName -C $dirName


