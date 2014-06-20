#!/usr/bin/env bash
# coding=utf-8
#
# 冷备份数据库 
#
# @date 2014-06-16
# @auth zhaigy@ucweb.com

set -e

DIR=$(cd $(dirname "$0"); cd ..; pwd)
cd $DIR

# mysql://uhp:uhp@hadoop2:3306/uhp?charset=utf8
user_passwd=$( cd $DIR/uhpcommon && python -c "import config; print config.connection" )

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

mysql -u "$user" -p"$passwd" -h "$host" -P $port $db
