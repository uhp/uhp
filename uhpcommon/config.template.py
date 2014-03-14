#!/usr/bin/env python
# coding:utf-8
import os 

uhphome = os.getenv('UHP_HOME')

template_dir = os.path.join(uhphome,"ansible","service","roles","conf","templates")

jar_dir = os.path.join(uhphome,"ansible","service","roles","jar","files")

#SQLITE的默认地址
#使用mysql的可以忽略
dbfile = os.path.join(uhphome,"db","sqlite.db")

#connection = "sqlite:///"+dbfile
#connection = "mysql://uhp:uhp@hadoop2:3306/uhp_qjw?charset=utf8"
connection = "mysql://uhp:uhp@hadoop2:3306/uhp?charset=utf8"

mq_host="localhost"
mq_port=4000

rmhost="vdc21"
rmport="50888"

#uhpweb dir
web_log_dir = os.path.join(uhphome,"logs","web")
web_log_file = "uhpweb.log"
web_bind_host = "0.0.0.0"
web_bind_port = 59990

# for worker
service_path = os.path.join(uhphome,"ansible","service")
ansible_host_list = os.path.join(uhphome,"inventor/mysqlinventory.py")
worker_thread_numb = 10

# for monitor
monitor_script_checkport = os.path.join(uhphome, "uhpmonitor/script/nt.sh")
monitor_thread_numb = 10
monitor_timer_interval = 10
port_key_flag = "file://%s/uhpmonitor/conf/port_key_flag.txt" % uhphome
monitor_process_timeout = 10


#USE FOR DEBUG

#fade_add_del=True
fade_add_del=False

#fade_windows=True
fade_windows=False
