uc-hadoop-platform
==================

##UHP是什么？

UHP是UC Hadoop Platfrom的缩写,是用于管理Hadoop的工具。UHP由UcWeb自主研发,是一个以Hadoop为核心的大数据平台,囊括了Zookeeper,Hdfs,Yarn,Hbase,Hive,Impala等常用服务,后续会根据需要添加更多的诸如storm,spark等的大数据相关的服务。

## UHP的一些特性

*   UHP是主要以Python写作的应用软件，通过Web服务和Daemon程序管控Hadoop。
*   UHP部署在单台机器上，UHP不需要和Hadoop主机部署在相同机器上，但习惯上是部署在一起的。
*   UHP和Hadoop没有强的依赖关系，UHP程序崩溃不会影响Hadoop运行。
*   UHP期望是无单点故障的，它的主要数据存储在Mysql中，所以强烈建议Mysql部署成主主互备。  
    如果UHP所在机器故障，在另一个机器Git代码，连上原有数据库，启动即可继续服务。
*   UHP使用Ansible脚本执行任务，使用Yum安装Cloudera的CDH。
*   UHP安装在单一用户下，要求此用户有sudo权限。



## 更多

[WIKI](https://github.com/uhp/uhp/wiki)

[UHP介绍](https://github.com/uhp/uhp/wiki/UHP介绍)

[UHP的模块](https://github.com/uhp/uhp/wiki/UHP的模块)

[使用UHP](https://github.com/uhp/uhp/wiki/使用UHP)

