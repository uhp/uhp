#!/usr/bin/env bash
# coding=utf-8

[ -z "$UHP_HOME" ] && source $HOME/.bash_profile 

[ -z "$UHP_HOME" ] && {
    echo "UHP_HOME not set."
    exit 1
}
echo "UHP_HOME=$UHP_HOME"

OLD_DIR=$(pwd)
cd $UHP_HOME;

sh bin/start-web.sh
sh bin/start-worker.sh
sh bin/start-monitor.sh

