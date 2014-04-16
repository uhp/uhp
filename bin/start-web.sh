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

app=`basename $0 .sh`
# app=web
app=${app#*-}

mkdir -p logs/$app pids/$app

cd uhp$app
nohup python uhp${app}.py >$UHP_HOME/logs/web/stdout 2>&1 &

sleep 1
pid=`ps -ef|grep uhp$app.py|grep -v grep|awk '{print \$2;}'`
[ -z "$pid" ] && {
    echo "Start Fail"
    exit 1
}

echo "PID: $pid"
echo "Start OK"
