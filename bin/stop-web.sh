#!/usr/bin/env bash
# coding=utf-8

[ -z "$UHP_HOME" ] && source $HOME/.bash_profile 

[ -z "$UHP_HOME" ] && {
    echo "UHP_HOME not set."
    exit 1
}
echo "UHP_HOME=$UHP_HOME"

app=`basename $0 .sh`
# app=web
app=${app#*-}

pid=`ps -ef|grep uhp$app.py|grep -v grep|awk '{print \$2;}'`
[ -z "$pid" ] && {
    echo "uhpweb not running"
    exit 0
}

kill $pid

echo -n "waitint."
for ((i=0;i<10;i++)); do
    sleep 1
    pid=`ps -ef|grep uhp$app.py|grep -v grep|awk '{print \$2;}'`
    [ -z "$pid" ] && {
        echo
        echo "Stop OK"
        exit 0
    }
    echo -n "."
done

echo
echo "Stop Fail"
echo "PID: $pid"
exit 1
