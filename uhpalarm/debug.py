#!/usr/bin/env python
# coding=utf-8

import os
import sys
commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir) 


import database
from model.alarm import Alarm
from model.host_group_var import GroupVar
from model.instance import Instance


session = database.getSession()

#session.merge(Instance("ganglia","hadoop2","gmetad",Instance.STATUS_STOP))
session.merge(Instance("ganglia","hadoop3","gmetad",Instance.STATUS_STOP))
#session.merge(Instance("ganglia","hadoop2","gmond",Instance.STATUS_STOP))
#session.merge(Instance("ganglia","hadoop3","gmond",Instance.STATUS_STOP))
#session.merge(Instance("ganglia","hadoop1","gmond",Instance.STATUS_STOP))
#session.merge(Instance("ganglia","hadoop4","gmond",Instance.STATUS_STOP))
#session.merge(Instance("ganglia","hadoop5","gmond",Instance.STATUS_STOP))

#session.merge(Instance("ganglia","hadoop2","datasource",Instance.STATUS_STOP))
#session.merge(Instance("ganglia","hadoop3","datasource",Instance.STATUS_STOP))

#session.merge(Alarm("check load", "max(load_one,0.5,0.8)","send_mail","*"))
#session.merge(Alarm("check memory", "max(load_one,0.5,0.8)","send_mail","*"))

#添加特殊的ganglia变量

#session.merge(GroupVar("all","ganglia","cluster_name","test_hadoop",0,""))
#session.merge(GroupVar("all","ganglia","data_source_ip","10.1.74.45",0,""))
#session.merge(GroupVar("all","ganglia","gmond_port","8649",0,""))
#session.merge(GroupVar("all","ganglia","gmetad_rras","RRA:AVERAGE:0.5:4:120,RRA:AVERAGE:0.5:40:1008,RRA:AVERAGE:0.5:240:336,RRA:AVERAGE:0.5:5760:376",1,""))
#session.merge(GroupVar("all","ganglia","gmond_python","",1,""))
#groups['all']['vars']['ganglia__cluster_name'] = "test_hadoop"
#groups['all']['vars']['ganglia__data_srouce_ip'] = "10.1.74.45"
#groups['all']['vars']['ganglia__gmond_port'] = 8649
#groups['all']['vars']['ganglia__gmetad_rras'] = ['RRA:AVERAGE:0.5:4:120','RRA:AVERAGE:0.5:40:1008','RRA:AVERAGE:0.5:240:336','RRA:AVERAGE:0.5:5760:376']
#groups['all']['vars']['ganglia__gmond_python'] = [{"name":"example","params":{"a":100,"b":"temp"},"collection_group":[{"collect_once":"yes","collect_every":10,"time_threshold":10,"metric":[{"name":"PyConstant_Number","value_threshold":1.0}]},{"collect_once":"no","collect_every":10,"time_threshold":10,"metric":[{"name":"PyRandom_Numbers","value_threshold":1.0}]}]},{"name":"example2","params":{"a":100,"b":"temp"},"collection_group":[{"collect_once":"yes","collect_every":10,"time_threshold":10,"metric":[{"name":"qjw_Number","value_threshold":1.0}]},{"collect_once":"no","collect_every":10,"time_threshold":10,"metric":[{"name":"qjw_Numbers","value_threshold":1.0}]}]}]


session.commit()
session.close()
