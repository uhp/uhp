# MySql主主互备

Ver：5.1+

## 安装

### 安装

    yum install mysql mysql-server -y

### 启动

    /etc/init.d/mysqld start

### 随机启动

    chkconfig --list | grep mysqld
    chkconfig --add mysqld
    chkconfig mysqld on

## 配置

`su - mysql`  
`vi my.cnf`

### 主主互备

参考：<http://showerlee.blog.51cto.com/2047005/1187693>

1.  在第一台机器上

	*	修改配置
	
			[mysqld]
			datadir=/var/lib/mysql
			socket=/var/lib/mysql/mysql.sock
			user=mysql
			symbolic-links=0
			log-bin=/var/log/mysql/bin.log
			server-id=1
			binlog-ignore-db=mysql
			# 用于自增长的id字段，防止同时增加记录的冲突
			auto-increment-increment=2
			auto-increment-offset=1
	
			[mysqld_safe]
			log-error=/var/log/mysqld.log
			pid-file=/var/run/mysqld/mysqld.pid

	*	备份账户

			grant replication slave on *.* to 'slave'@'10.34.102.%' identified by 'slave';
	
	*	导出数据

			mysqldump -u root -proot --opt --skip-lock-tables --flush-logs --all-database > /root/allbak.sql

	*	把导出数据转到2号机

	*	重启
	
			service mysqld restart

2.	在第二台机上

	*	导入

			/usr/local/mysql/bin/mysql -u root -p123456 < /root/allbak.sql

	*	重启
	*	账户操作

			stop slave;  
			CHANGE MASTER TO MASTER_HOST='host1', MASTER_PORT=3306, MASTER_USER='slave',  MASTER_PASSWORD='slave';
			start slave;

3.	在第一台机上

		stop slave;
		change master to master_host='pagediff3', master_user='slave',master_password='slave';
		start slave;

4.	验证

		show slave status\G;
		# 搜索这三行，如下则主主互备配置成功
		Slave_IO_State: Waiting for master to send event
		Slave_IO_Running: Yes
		Slave_SQL_Running: Yes