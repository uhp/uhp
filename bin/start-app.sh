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
# app=worker
app=${app#*-}

mkdir -p logs/$app pids/$app

chmod a+x ./uhp$app/$app.py
./uhp$app/$app.py

ok="false"
for ((i=0;i<10;i++)); do
    pidfile=$(ls ./pids/${app}/*.pid 2>/dev/null)
    [ -n "$pidfile" ] && {
        pid=$(cat ./pids/${app}/*.pid 2>/dev/null)
        echo "PID: $pid"
        echo "Start OK"
        ok="true"
        break
    }
    sleep 1
done

cd $OLD_DIR
[ "$ok" == "true" ] && exit 0

echo "Start Fail"
exit 1
