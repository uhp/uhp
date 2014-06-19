#sh ./mnt.sh "1:59990,-4000:uhpweb.py"
#sudo sh ./mnt.sh 44:8649:gmond  45:8651:gmetad 
sudo sh ./mnt.sh 44:8649:gmond  74:59200:HiveServer\b

#check_ports=$(sudo netstat -nplt 2>/dev/null | grep LISTEN | grep tcp | grep -v ansible | awk '{ port=sub(/.*:/,"",$4); pid=sub(/\/.*/,    "",$7); if($7 != "-") printf("%s=%s\n",$7,$4);}'|sort|uniq)

#echo $check_ports

#check_ports=$(sudo ss -nplt 2>/dev/null | grep -v ansible | awk '{ port=sub(/.*:/,"",$4); pid=sub(/\/.*/,    "",$7); if($7 != "-") printf("%s=%s\n",$7,$4);}')

#LISTEN     0      10                        *:8651                     *:*      users:(("gmetad",1844,0))
#LISTEN     0      10                        *:8652                     *:*      users:(("gmetad",1844,1))
#LISTEN     0      128         192.168.158.134:50030                    *:*      users:(("java",3822,172))

#check_ports=$( sudo ss -nplt 2>/dev/null|sed -e 1d |grep -v ansible|awk '{ sub(/.*:/,"",$4); sub(/.*\",/,"",$6);sub(/,.*/,"",$6); printf("%s=%s\n",$6,$4);}'|sort|uniq)
#echo $check_ports
