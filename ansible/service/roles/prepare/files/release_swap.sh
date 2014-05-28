#!/bin/bash

DEV=`swapon -s|grep dev|awk '{print $1}'`
swapoff   $DEV
swapon -a
