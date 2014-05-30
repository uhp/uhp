#!/usr/bin/env bash

myname=${0##.*/}

USAGE=<<EOS
    usage: $myname "insid:port,port,-port:key" "..."
      @param: -port 端口可以不存在 
      
      return: insid:state:msg\n...
      @state: 0 ok, 1 必要端口不全, 2 进程不存在 
EOS

[ $# -eq 0 ] && { 
    echo $USAGE
    echo "0,,params error"; 
    exit 1; 
}

# port pid
# tcp        0      0 127.0.0.1:4000              0.0.0.0:*                   LISTEN      30448/python
check_ports=$(netstat -nplt 2>/dev/null | grep LISTEN | grep tcp | awk '{ port=sub(/.*:/,"",$4); pid=sub(/\/.*/,"",$7); if($7 != "-") printf("%s=%s\n",$7,$4);}' | sort)

retu=()

# 通过Key找到进程，再核对端口
i=0
for param in $@; do
    array=(${param//:/ })
    insid=${array[0]}
    ports=(${array[1]//,/ })
    key=${array[2]}
    # 'zhaigy   19010     1  0 May29 ?        00:08:10 /home/zhaigy/develop/uhp/vpy/bin/python uhpweb.py'
    pids=$(ps -ef | grep -v grep | grep -v mnt.sh | grep -e "$key" | awk '{print $2}')
    # pids=$(ps -ef | grep -e "$key" | awk '{print $2}')
    [[ pids == "" ]] && {
        retu[$i]="$insid:2:进程[特征:$key]不存在"
        continue   
    }
    for pid in $pids; do
        # 尝试此PID
        echo $pid
        # 查找端口
        pid_ports=()
        for pid_port in $check_ports; do
            [[ $pid_port == "$pid=*" ]] && {
                port=${pid_port##.*=}
                pid_ports+=($port)
            }
        done

        # 匹配端口要求
        exist_ports=()
        noexist_ports=()
        for port in ${ports[@]}; do
            no_muste="true"
            [[ ${port:0:1} == "-" ]] && port=${port:1}
            find_it="false"
            for pid_port in ${pid_ports[@]}; do
                [[ port == pid_port ]] && {
                    exists_ports+=($port)
                    find_it="true"
                    break
                }
            done
            [[ $find_it != "true" ]] && noexist_port+=($port) 
        done
    done
done

#echo $check_ports

##|grep -E '9922|8000'
#gstr=""
#for port in $@; do
#    [ -z "$gstr" ] || gstr="${gstr}|"
#    gstr="${gstr}$port"
#done
##echo $gstr
#
#check_ports=$(netstat -nplt 2>/dev/null | grep LISTEN | grep tcp | awk '{print $4}'|awk 'BEGIN{FS=":"}; {print $NF}' | sort | uniq | grep -E "$gstr")
#
#for port in $@; do
#    for check_port in $check_ports; do
#        if [ "$port" == "$check_port" ]; then
#            echo $port
#            break
#        fi
#    done
#done

#|grep -E '9922|8000'
