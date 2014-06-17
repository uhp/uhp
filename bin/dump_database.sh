#!/usr/bin/env bash
# coding=utf-8
#
# 冷备份数据库 
#
# @date 2014-06-16
# @auth zhaigy@ucweb.com

set -e

[ "$UHP_HOME" == "" ] && { echo "UHP_HOME not defined"; exit 1; }

cd $UHP_HOME/uhpcommon
# mysql://uhp:uhp@hadoop2:3306/uhp?charset=utf8
user_passwd=$(python -c "import config; print config.connection")

temp=${user_passwd}
temp=${temp##*\/\/}
temp=${temp%%@*}
user=${temp%%:*}
passwd=${temp##*:}

temp=${user_passwd}
temp=${temp##*@}
host=${temp%%:*}

temp=${user_passwd}
temp=${temp##*:}
port=${temp%%/*}

temp=${user_passwd}
temp=${temp##*/}
db=${temp%%\?*}

#user=uhp
#passwd=uhp
#host=hadoop2
#port=3306
#db=uhp
#charset=utf8

cd $UHP_HOME
mkdir -p db

dt=$( date +"%Y%m%d_%H%M%S" )

#mysqldump -u "$user" -p"$passwd" -h "$host" -P $port --opt --skip-lock-tables --flush-logs $db > ./db/back_${db}_${dt}.sql
mysqldump -u "$user" -p"$passwd" -h "$host" -P $port --opt --skip-lock-tables $db > ./db/back_${db}_${dt}.sql
#/usr/local/mysql/bin/mysql -u root -p123456 < /root/allbak.sql

find ./db/ -name "back_*.sql" -ctime +10 -exec rm -f {} \;

