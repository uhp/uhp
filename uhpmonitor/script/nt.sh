#!/usr/bin/env bash
#sleep 10
[ $# -eq 0 ] && exit 1
#|grep -E '9922|8000'
gstr=""
for port in $@; do
    [ -z "$gstr" ] || gstr="${gstr}|"
    gstr="${gstr}$port"
done
#echo $gstr

check_ports=$(netstat -nplt 2>/dev/null | grep LISTEN | grep tcp | awk '{print $4}'|awk 'BEGIN{FS=":"}; {print $NF}' | sort | uniq | grep -E "$gstr")

for port in $@; do
    for check_port in $check_ports; do
        if [ "$port" == "$check_port" ]; then
            echo $port
            break
        fi
    done
done

#|grep -E '9922|8000'
