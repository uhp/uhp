#!/usr/bin/env bash
# coding=utf-8

[ -z "$UHP_HOME" ] && source $HOME/.bash_profile 

[ -z "$UHP_HOME" ] && {
    echo "UHP_HOME not set."
    exit 1
}
#echo "UHP_HOME=$UHP_HOME"

OLD_DIR=$(pwd)
cd $UHP_HOME;

app=`basename $0 .sh`
# app=worker
app=${app#*-}

echo "------------------------------"
echo "- START $app"
echo "------------------------------"

mkdir -p logs/$app pids/$app

# check pid file
pidfile=$(ls ./pids/${app}/*.pid 2>/dev/null)
[ -n "$pidfile" ] && {
    echo "WARN: pidfile[$pidfile] exists!" 
    pid=$(cat ./pids/${app}/*.pid 2>/dev/null)
    exists=`ps ux|awk '{print $2}'|grep ^$pid$|wc -l`
    if [ "$exists" != "0" ]; then
        echo "ERROR: Progress is exists!" 
        exit $exists
    fi
    # 删除不存在的PID
    echo "WARN: try run it"
    rm -f $pidfile
}

chmod a+x ./uhp$app/$app.py
./uhp$app/$app.py

ok="false"
for ((i=0;i<10;i++)); do
    pidfile=$(ls ./pids/${app}/*.pid 2>/dev/null)
    [ -n "$pidfile" ] && {
        pid=$(cat ./pids/${app}/*.pid 2>/dev/null)
        echo "PID: $pid"
        ok="true"
        break
    }
    sleep 1
done

cd $OLD_DIR
[ "$ok" == "true" ] && {
    echo "Start OK"
} || {
    echo "Start Fail"
}
echo "------------------------------"
[ "$ok" == "true" ]
exit $?
