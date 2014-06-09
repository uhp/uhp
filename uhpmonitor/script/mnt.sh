#!/usr/bin/env bash
set -e
myname=${0##.*/}

USAGE=<<EOS
    usage: $myname "insid:port,port,-port:key" "..."
      @param: -port 端口可以不存在 
      
      return: insid:state:msg\n...
        @state: 0=ok, 1=必要端口不全, 2=进程不存在, 3=其它错误
        @msg  : {pid:,exist_port:[],unexist_port:[],...}
EOS

[ $# -eq 0 ] && { 
    # echo $USAGE
    echo "0:3:{\"pid\":0,\"exist_port\":[],\"unexist_port\":[],\"msg\":\"params error\"}"; 
    exit 0; 
}

# pid=port
# tcp        0      0 127.0.0.1:4000              0.0.0.0:*                   LISTEN      30448/python
check_ports=$(netstat -nplt 2>/dev/null | grep LISTEN | grep tcp | grep -v ansible | awk '{ port=sub(/.*:/,"",$4); pid=sub(/\/.*/,"",$7); if($7 != "-") printf("%s=%s\n",$7,$4);}')

retu=()

# 通过Key找到进程，再核对端口
for param in $@; do
    array=(${param//:/ })
    insid=${array[0]}
    ports=(${array[1]//,/ })
    key=${array[2]}
    # 'zhaigy   19010     1  0 May29 ?        00:08:10 /home/zhaigy/develop/uhp/vpy/bin/python uhpweb.py'
    pid=$(ps -ef | grep -v grep | grep -v mnt.sh | grep -i -e "$key" | head -n 1 | awk '{print $2}')
    [[ $pid == "" ]] && {
        retu+=("{\"insid\":$insid,\"state\":2,\"msg\":{\"pid\":0,\"exist_port\":[],\"unexist_port\":[],\"msg\":\"进程[特征:$key]不存在\"}}")
        continue   
    }
   
    # 查找端口
    pid_ports=()
    for pid_port in $check_ports; do
        pid_port=(${pid_port//=/ })
        [[ $pid == ${pid_port[0]} ]] && {
            port=${pid_port[1]}
            pid_ports+=($port)
        }
    done

    # 匹配端口要求
    exist_port=()
    unexist_port=()
    lack_port=() # 缺少的端口
    state=0

    for port in ${ports[@]}; do
        must="true"
        [[ ${port:0:1} == "-" ]] && {
            port=${port:1}
            must="false"
        }
        find_it="false"
        for pid_port in ${pid_ports[@]}; do
            [[ $port == $pid_port ]] && {
                exist_port+=($port)
                find_it='true'
                break
            }
        done
        [[ "$find_it" != "true" ]] && {
            unexist_port+=($port) 
            [[ $must == "true" ]] && { 
                lack_port+=($port); 
                state=1; 
            }
        }
    done
   
    exist_port_str=${exist_port[@]// /,}
    unexist_port_str=${unexist_port[@]// /,}
    lack_port_str=${lack_port[@]// /,}
    pid_ports_str=${pid_ports[@]// /,}
    #check_ports_str=${check_ports// /,}
    
    msg="all_is_ok"
    [[ $lack_port_str != "" ]] && {
        msg="缺少必要的端口[$lack_port_str]"
    }

   retu+=("{\"insid\":$insid,\"state\":$state,\"msg\":{\"pid\":$pid,\"exist_port\":[$exist_port_str],\"unexist_port\":[$unexist_port_str],\"pid_port\":[$pid_ports_str],\"msg\":\"$msg\"}}")

done

echo -n ":CHECKSTART:["
first="true"
for r in ${retu[@]}; do
    [[ $first == "true" ]] && {
        first="false"
    } || {
        echo -n ","
    }
    echo -n $r
done
echo "]:CHECKEND:"
