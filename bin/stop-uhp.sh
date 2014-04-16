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

sh bin/stop-web.sh
sh bin/stop-worker.sh
sh bin/stop-monitor.sh

