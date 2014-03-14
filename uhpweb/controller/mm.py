# -*- coding: UTF-8 -*-
import os
import sys
import snakemq
import snakemq.link
import snakemq.packeter
import snakemq.messaging
import snakemq.message
commondir=os.path.join(os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)
import config
    
#添加删除服务
#删除提交任务，并且轮询任务是否执行完成
#如果任务执行完成，就删除

#thread.start_new_thread(fun,obj)


def send(msg, ttl=None):
    if config.fade_windows:
        return True;
    link = snakemq.link.Link()
    link.add_connector((config.mq_host, config.mq_port))
    packeter = snakemq.packeter.Packeter(link)
    messaging = snakemq.messaging.Messaging('uhpweb', "", packeter)

    msg_num = [1]
    def _inner_on_message_sent(conn_id, ident, message_uuid):
        link.stop()
        msg_num[0] = 0

    messaging.on_message_sent.add(_inner_on_message_sent)
    
    message = snakemq.message.Message(msg, ttl=ttl)
    messaging.send_message("worker", message)

    link.loop(runtime=3)
    link.cleanup()
   
    return msg_num[0] == 0 

# id: taskid, int type
def kill_task(taskid):
    msg = 'killtask:%d' % taskid
    return send(msg)

#print send("1,2")
