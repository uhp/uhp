# -*- coding: UTF-8 -*- 


import json
import os.path, logging, sys
import config
import random
import commands
import time

app_log = logging.getLogger("tornado.application")

def get_template_file(host,dir,file):
    ts=int(time.time())
    file_list=[]
    file_list.append(file)
    shell_command = "sh %s/ansible/service/script/build_template_file.sh %s %s '%s' %s %s" % (config.uhphome,host,dir,json.dumps(file_list),ts,"flase" )
    print shell_command
    app_log.info(shell_command)
    (status,output)=commands.getstatusoutput( shell_command )
    if status == 0 :
        dest = "/tmp/%s/%s/%s/%s" % (ts,host,dir,file) 
        app_log.info(dest)
        if os.path.exists(dest) and os.path.isfile(dest) :
            content=open(dest,"r").read()
            return (content,output)
    return ("",output)
    
def download_template_file(host,dir):
    ts=int(time.time())
    file_list=[]
    #add all file
    dirPath = os.path.join(config.template_dir,dir)
    for file in os.listdir(dirPath):
        filePath = os.path.join(dirPath,file)
        if os.path.exists(filePath) and os.path.isfile(filePath):
            file = file.replace(".j2","")
            file_list.append(file);
    #
    shell_command = "sh %s/ansible/service/script/build_template_file.sh %s %s '%s' %s %s" % (config.uhphome,host,dir,json.dumps(file_list),ts,"true" )
    app_log.info(shell_command)
    print shell_command
    (status,output)=commands.getstatusoutput( shell_command )
    if status == 0 :
        return ("/tmp/%s_%s_%s.tar.gz" % (ts,host,dir),output)
    return ("",output)

if __name__ == '__main__':
    #print get_template_file("hadoop1","hbase","hbase-env.sh")
    print download_template_file("hadoop1","hadoop")
