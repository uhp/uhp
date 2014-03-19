uc-hadoop-platform
==================

##UHP是什么？

UHP是UC Hadoop Platfrom的缩写，是公司内部共用的Hadoop基础平台。
为什么需要UHP?
1. 节约硬件成本：建设一个Hadoop集群需要较多的硬件成本，中小业务单独建设集群不现实。
2. 节约运维成本：Hadoop需要专业的工程师运维，学习成本高，运维难度大。
3. 数据共享：集群间的数据共享非常麻烦，多业务共用集群有利于数据共享。

UHP的目标：
1. 实现多租户接入，完善底层鉴权和权限，让数据共享更灵活更安全。
2. 降低运维成本，让Hadoop平台运维自动化，安装部署监控一体化。
3. 提供基本的大数据处理工具（作业调度、Hive查询、Impala查询）。



#开始使用

##启动

###依赖
	
	本项目需要python2.6或以上,pip,一个可用的mysql，请自行安装。
	设置UHP_HOME环境变量,指向本项目的根目录(请不要随意更改根目录,否则可能会导致不可用)。
    设置ANSIBLE_CONFIG环境变量，指向$UHP_HOME/conf/ansible.cfg。
	初次启动请运行bin/init.sh安装依赖，同时会创建一系列的运行目录等

###数据库初始化

    修改uhpcommon/config.py中的connection选项使之能正确地连接mysql
	运行以下命令，进行初始化：
		
		python uhpcommon/database.py

###安装本地库(可选)

	UHP选用CDH的yum安装作为底层。安装过程中会需要连接CDH官网下载JAR包。
	由于众所周知的原因，可能会导致连接CDH官方的网站缓慢。
	而且大批量地安装连接CDH官网也会导致带库吃紧。
	安装本地库，可以极大地减轻带宽压力。
	
	安装:
	1. 准备一个所有机器都能访问的HTTP服务。
	2. 运行以下命令开始安装本地库:
		
		sudo sh bin/createrepo.sh /xx/xx/xx 5 
		(第一个参数请正确填写要下载的本地目录,第二个参数填写下载centos5或者centos6的仓库。
		如果，集群中既有centos5的系统和centos6的系统,请下载这两个仓库)
	
	3. 在你指定的下载目录会发现下载好的文件,格式为格式如下：
	
		└── 5
			└── cloudera-cdh4
				└── cloudera-cdh4
					└── RPMS
						├── noarch
		...
		
		将这个文件夹移动到你的HTTP的root目录，然后尝试通过浏览器访问，看能不能访问到相关目录。
		如果可以，那本地仓库就安装成功了。
	
	如果,网络状况太差，下载失败。可以使用我们准备好的uhp_repo.tar.gz包，直接在HTTP服务的本地根目录解压即可。

###启动uhpweb界面：
	
1. 修改uhpcommon/config.py的connection
   *  确保配置的数据库路径是存在的
   *  可以修改文件中User表的数据，配置需要的用户名和密码
   
2. 运行以下命令,会建立数据库的表信息
	
	python uhpcommon/database.py
	
3. 创建配置文件并根据实际需要修改端口或者配置
	
		cp uhpweb/etc/uhpweb.conf.template uhpweb/etc/uhpweb.conf
	
4. 运行以下命令启动web程序:
	 
		cd uhpweb;python uhpweb.py

5. 访问http://xxxx:59990即可


###uhpworker启动流程:

TODO
	 
###uhpmonitor启动流程:

TODO

##安装服务

###界面操作指导

	访问uhpweb的网址 用户名初始密码 admin/admin
	初次访问请设置必要的全局变量
	路径(管理员界面-设置),修改以下关键变量:
		
		ansible_ssh_user:*用于登录到其它机器的用户名称
		ansible_ssh_port:*ssh的登录端口
		ansible_ssh_pass:*ssh的登录密码
		ansible_sudo_pass:*ssh登录后的sudo密码
		local_repo_enabled:*是否使用本地仓库。如果，使用本地仓库，请填写local_http_url
		local_http_url:*如果使用本地仓库，本地仓库的地址

		java_tar:*添加机器的时候.检查到没有java的话会安装的java的tar包。请填写绝对路径。
		java_untar_floder:*安装java的时候tar包解压的名称。推荐安装示例形式填写

####各个模块

#####服务：

	管理和安装各种服务。
	
#####机器:

	管理各个机器。

#####任务：

	查看所有运行的任务。
	
#####设置：

	配置一些全局配置。
	
#####模板：

	修改服务配置文件的模板。
	
#####右上角-高级-手动修改：

	针对一些意外发生的bug，可以方便地修改一些数据库的状态。
