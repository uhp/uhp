#!python
# coding=utf8

adminmenus = {
        "name":"admin", "display":"管理员", "href":"/admin",
        "submenus":[
            {"name":"service", "display":"服务", "href":"#admin-service"},
            {"name":"host", "display":"机器", "href":"#admin-host"},
            {"name":"task", "display":"任务", "href":"#admin-task"},
            {"name":"setting", "display":"设置", "href":"#admin-setting"},
            {"name":"template", "display":"模板", "href":"#admin-template"}
            ]    
         }

usermenus = {"name":"user", "display":"用户", "href":"/user",
        "submenus":[
            #{"name":"info", "display":"概况", "href":"#user-info"},
            {"name":"hdfs", "display":"存储", "href":"#user-hdfs"},
            {"name":"yarn", "display":"作业", "href":"#user-yarn"}
            ]    
         }


#由于基本不修改，所以不存放在数据库
#保存了所有的素服和角色
services = [
    {"name":"zookeeper", 
     "role": ["zookeeper"],
     "actions":[{"name":"start","display":"启动","tooptip":"开启集群"},
              {"name":"stop","display":"停止","tooptip":"关闭集群"},
              {"name":"restart","display":"重启","tooptip":"重启集群"}], 
     "instanceActions":[{"name":"start","display":"启动","tooptip":""},
                        {"name":"stop","display":"停止","tooptip":""},
                        {"name":"restart","display":"重启","tooptip":""}],
     "dependence" : []
     },
    {"name":"hdfs", 
     "role": ["qjm","namenode","datanode"],
     "actions":[{"name":"format","display":"格式化","tooptip":"格式化所有组件。谨慎执行！"},
                {"name":"start","display":"启动","tooptip":""},
                {"name":"stop","display":"停止","tooptip":""},
                {"name":"restart","display":"重启","tooptip":""},
                {"name":"rollrestart","display":"滚动重启","tooptip":"滚动重启所有的datanode."},
                {"name":"initha","display":"重置HA","tooptip":"分发hdfs的SSH，重置在ZK的HA状态。"},
                {"name":"init","display":"初始化","tooptip":"创建hdfs上的一些必要的目录。"},
                {"name":"check","display":"检查","tooptip":"执行读写操作，检查是否可用。"}], 
     "instanceActions":[{"name":"start","display":"启动","tooptip":""},
                        {"name":"stop","display":"停止","tooptip":""},
                        {"name":"restart","display":"重启","tooptip":""}],
     "dependence" : ["zookeeper"],
     "web" : [{"role":"namenode","port":"dfs_namenode_http_address_port"}]
     },
    {"name":"yarn", 
     "role": ["resourcemanager","nodemanager","historyserver"],
     "actions":[{"name":"init","display":"初始化","tooptip":"创建yarn所需要的hdfs目录。"},
                {"name":"start","display":"启动","tooptip":""},
                {"name":"stop","display":"停止","tooptip":""},
                {"name":"restart","display":"重启","tooptip":""},
                {"name":"rollrestart","display":"滚动重启","tooptip":"滚动重启所有的nodemanager。"},
                {"name":"check","display":"检查","tooptip":"提交一个YARN作业并运行。"}],
     "instanceActions":[{"name":"start","display":"启动","tooptip":""},
                        {"name":"stop","display":"停止","tooptip":""},
                        {"name":"restart","display":"重启","tooptip":""}],
     "dependence" : ["zookeeper","hdfs"],
     "web" : [{"role":"resourcemanager","port":"yarn_nm_webapp_port"},
              {"role":"historyserver","port":"mapreduce_jobhistory_webapp_port"}]
     },
    {"name":"hbase",
     "role":["hbasemaster","regionserver"],
     "actions":[{"name":"init","display":"初始化","tooptip":"创建hbase所需要的hdfs目录。"},
                {"name":"start","display":"启动","tooptip":""},
                {"name":"stop","display":"停止","tooptip":""},
                {"name":"restart","display":"重启","tooptip":""},
                {"name":"check","display":"检查","tooptip":"执行hbase的基本操作，检查hbase是否可用。"}], 
     "instanceActions":[{"name":"start","display":"启动","tooptip":""},
                        {"name":"stop","display":"停止","tooptip":""},
                        {"name":"restart","display":"重启","tooptip":""}],
     "dependence" : ["zookeeper","hdfs"],
     "web" : [{"role":"hbasemaster","port":"hbase_master_info_port"},
              {"role":"regionserver","port":"hbase_resigionserver_info_port"}]
     },
    {"name":"hive",
     "role":["hiveserver","hiveserver2","hivemetastore"],
     "actions":[{"name":"initmysql","display":"初始化数据库","tooptip":"初始化hive的元数据库。"},
                {"name":"init","display":"初始化","tooptip":"创建HDFS目录。"},
                {"name":"start","display":"启动","tooptip":""},
                {"name":"stop","display":"停止","tooptip":""},
                {"name":"restart","display":"重启","tooptip":""},
                {"name":"check","display":"检查","tooptip":"执行hive的sql语句，检查hive是否可用。"}], 
     "instanceActions":[{"name":"start","display":"启动","tooptip":""},
                        {"name":"stop","display":"停止","tooptip":""},
                        {"name":"restart","display":"重启","tooptip":""}],
     "dependence" : ["hdfs","yarn"]
     },   
     {"name":"impala",
     "role":["impalastatestore","impalaserver"],
     "actions":[{"name":"start","display":"启动","tooptip":""},
                {"name":"stop","display":"停止","tooptip":""},
                {"name":"restart","display":"重启","tooptip":""},
                {"name":"check","display":"检查","tooptip":"执行简单查询,检查impala是否可用。"}
                ], 
     "instanceActions":[{"name":"start","display":"启动","tooptip":""},
                        {"name":"stop","display":"停止","tooptip":""},
                        {"name":"restart","display":"重启","tooptip":""}],
     "dependence" : ["hdfs","hive"],
     "web" : [{"role":"impalastatestore","port":"impala_state_store_web_port"}]
     },     
     {"name":"client",
     "role":["zookeeper-client","hadoop-client","hbase-client","hive-client","impala-client"],
     "actions":[], 
     "instanceActions":[{"name":"config","display":"分发配置","tooptip":"分发配置文件"}],
     "dependence" : []
     },       
    ]   

role_check_map = { 
    "zookeeper" : { "min" : 1 },
    "qjm" : { "min" : 1 },
    "namenode" : { "equal" : 2 },
    "datanode" : { "min" : 1 },
    "resourcemanager" : { "equal" : 1 }, 
    "nodemanager" : { "min" : 1 }, 
    "historyserver" : { "equal" : 1 }, 
    }

def get_service_from_role(role):
    for service in services:
        if role in service['role']:
            return service['name']

def get_role_from_service(now):
    for service in services:
        if service['name'] == now:
            return service['role']
