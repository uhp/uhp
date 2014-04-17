uhpApp.controller('HostsCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	//初始化各种数据
	$scope.$watch('tab',function(newValue,oldValue){
		if(newValue=="host")$scope.initHost();
		if(newValue=="role")$scope.initRole();
		if(newValue=="group")$scope.initGroup();
	});
	$scope.tabClass=function(tabName,suffix){
		if(suffix==null) suffix="";
		if($scope.tab==tabName) return "active "+suffix;
		else return "";
	}
	//初始化机器和角色的对应关系
	$scope.initHost=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/hosts',
	    }).success(function(response, status, headers, config){
	    	$scope.hosts = response['hosts'];
	    	$scope.initChosenHost()
	    	$scope.rackList={}
	    	for(var index in $scope.hosts){
	    		var temp = $scope.hosts[index];
	    		$scope.rackList[temp["info"]["rack"]]=1;
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送hosts请求失败");
	    });
	}
	$scope.initChosenHost=function(){
		var temp = $scope.chosenHost;
		$scope.chosenHost={}
		for(var host in $scope.hosts){
			if( temp!= null && host in temp ){
				$scope.chosenHost[host] = temp[host];
			}
			else{
				$scope.chosenHost[host] = false;
			}
		}
		if( $scope.chosenAllHost == null ){
			$scope.chosenAllHost = false
		}
	}
	$scope.initRole=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/host_role',
//	        url: '/statics/static_data/hostrole.json',
	    }).success(function(response, status, headers, config){
	    	$scope.roles = response['roles']
	    	$scope.serviceList = []
	    	for(var ser in $scope.roles){
	    		$scope.serviceList.push(ser)
			}
	    	if( $scope.chosenService == null ){
	    		$scope.chosenService = $scope.serviceList[0]
	    	}
	    	$scope.hostroles = response['hostroles']
	    	$scope.initHostRole(1)
	    	$scope.doing = response['doing']
	    	if($scope.doing!=null && $scope.doing.length !=0) $scope.isDoing=true;
	    	else $scope.isDoing=false;
	    }).error(function(data, status) {
	    	$rootScope.alert("发送host_role请求失败");
	    });
	}
	$scope.doingStatus=function(host,role){
		var temp=""
		angular.forEach($scope.doing, function(doingTask) {
			if( doingTask['host']==host && doingTask['role']==role) temp=doingTask['status'];
		})
		return temp
	}
	//通过hostroles保存的真实的关系初始化hostRoleMap的对应关系
	$scope.initHostRole=function(needOld){
		var oldMap = null;
		if( needOld != null && needOld == 1){
			oldMap = $scope.hostRoleMap ;
		}
		var map={};
		for(var host in $scope.hostroles){
			map[host]={};
			var roleList = $scope.hostroles[host]['role']
			for(var ser in $scope.roles ){
				for(var index in $scope.roles[ser]){
					var role = $scope.roles[ser][index];
					//为了避免刷新会丢失用户的选择加入值传递
					if( oldMap != null &&  ( host in oldMap) && (role in oldMap[host]) ){
						map[host][role] = oldMap[host][role];
					}
					else{
						if( inArray(roleList,role) ) {
							map[host][role]=true;
						}
						else {
							map[host][role]=false;
						}
					}
				}
			}
		}
		$scope.hostRoleMap = map;
	}
	$scope.initGroup=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/host_group',
	    }).success(function(response, status, headers, config){
	    	$scope.groups = response['groups'];
	    	$scope.hostgroups = response['hostgroups']
	    	$scope.initHostGroup();
	    }).error(function(data, status) {
	    	$rootScope.alert("发送host_group请求失败");
	    });
	}
	$scope.initHostGroup=function(){
		var map={};
		for(var host in $scope.hostgroups){
			map[host]={};
			var groupList = $scope.hostgroups[host]['group']
			for(var group in $scope.groups ){
				if( inArray(groupList,group) ) map[host][group]=true;
				else map[host][group]=false;
			}
		}
		$scope.hostGroupMap = map;
		$scope.nowGroup={}
	}
	
	$scope.filterHostBySearchInfo=function(hosts,search){
		if(search==null||search=="") return hosts;
		var ret={};
		angular.forEach(hosts, function(value, key) {
	        if( key.indexOf(search) >=0 || searchArray(value['info'],search) ) {
	            ret[key] = value;
	        }
	    });
		return ret;
	}
	//添加删除机器
	$scope.readyAddHost=function(){
		$scope.nowHost = {}
		$("#hostNewHostModal").modal();
	}
	$scope.addHost=function(){
		if( $scope.nowHost.hosts==null ){
			$rootScope.alert("机器不能为空", "now");
			return;
		}
		$http({
	        method: 'POST',
	        url: '/adminback/add_host',
	        params:{
	        	"hosts": $scope.nowHost.hosts.replace(new RegExp("\n","gm"),","),
	        	"user": $scope.nowHost.user,
	        	"port": $scope.nowHost.port,
	        	"passwd": $scope.nowHost.passwd,
	        	"sudopasswd":$scope.nowHost.sudopasswd
	        }
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
	    		$rootScope.beginProgress(response["runningId"],$scope.initHost);
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送add_host请求失败");
	    });
	}
	//添加机架
	$scope.readySetRack=function(){
		$scope.chosenHostStr=$scope.getChosenHostStr();
		if( $scope.chosenHostStr == "" ){
			$rootScope.alert("请选择机器", "now")
			return 
		}
		if( $scope.settingRack == null || $scope.settingRack == "" ){
			$rootScope.alert("请填写机架名称","warn")
			return 
		}
		$("#hostSetRackModal").modal();
	}
	$scope.setRack=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/set_rack',
	        params:{
	        	"hosts": $scope.chosenHostStr,
	        	"rack": $scope.settingRack
	        }
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败:"+response["msg"]);
	        }
	    	$scope.initHost()
	    }).error(function(data, status) {
	    	$rootScope.alert("发送请求失败");
	    });
	}
	//全选chosenAll
	$scope.$watch("chosenAllHost",function(newValue,oldValue){
		for(var host in $scope.chosenHost){
			$scope.chosenHost[host] = newValue;
		}
	})
	$scope.readyDelHost=function(){
		$scope.chosenHostStr=$scope.getChosenHostStr();
		if( $scope.chosenHostStr == "" ){
			$rootScope.alert("请选择机器","now")
			return 
		}
		$("#hostDelHostModal").modal();
	}
	$scope.getChosenHostStr=function(){
		ret=[];
		for(var host in $scope.chosenHost){
			if( $scope.chosenHost[host]) ret.push(host);
		}
		return ret.join(",");
	}
	$scope.delHost=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/del_host',
	        params:{
	        	"hosts": $scope.chosenHostStr
	        }
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败:"+response["msg"]);
	        }
	    	$scope.initHost()
	    }).error(function(data, status) {
	    	$rootScope.alert("发送请求失败");
	    });
	}
	$scope.readySendRepo=function(){
		$scope.chosenHostStr=$scope.getChosenHostStr();
		if( $scope.chosenHostStr.length == 0 ){
			$rootScope.alert("请选择机器", "now")
			return;
		}
		$("#sendRepoModal").modal()
	}
	$scope.sendRepo=function(){
		var instanceList = [] ; 
		for(var host in $scope.chosenHost){
			if( $scope.chosenHost[host]) {
				instanceList.push(host+"-prepare");
			}
		}
		$http({
	        method: 'GET',
	        url: '/adminback/send_action',
	        params:{
        		"service" : "prepare",
        		"taskName" : "repo",
        		"actionType" : "instance",
        		"instances" : instanceList.join(",")
	        }
	    }).success(function(response, status, headers, config){
	    	if(response["ret"] !="ok" ){
	        	$rootScope.alert("提交失败:"+response["msg"]);
	        }
	    	
	    }).error(function(data, status) {
	    	$rootScope.alert("发送请求失败");
	    });
	}
	
	
	
	
	//角色相关的函数
	$scope.filterHostBySearch=function(hosts,search){
		if(search==null||search=="") return hosts;
		var ret={};
		angular.forEach(hosts, function(value, key) {
	        if( key.indexOf(search) >=0 ) {
	            ret[key] = value;
	        }
	    });
		return ret;
	}
	$scope.readySetupInstance=function(){
		var del=[];
		var add=[];
		for(var host in $scope.hostroles){
			var roleList = $scope.hostroles[host]['role']
			for(var ser in $scope.roles ){
				for( var index in $scope.roles[ser]){
					var role = $scope.roles[ser][index]
					var oldRea = inArray(roleList,role);
					var newRea = $scope.hostRoleMap[host][role];
					if( oldRea && !newRea ){
						del.push({"host":host,"role":role});
					}
					if( !oldRea && newRea ){
						add.push({"host":host,"role":role});
					}
				}
			}
		}
		$scope.addInstance=add;
		$scope.delInstance=del;
		
		$scope.vars=[]
		console.log($scope.chosenService)
		if($scope.chosenService=="zookeeper"){
			for(var index in $scope.addInstance){
				var host = $scope.addInstance[index]['host'];
				
				var v={}
				v['service']=$scope.chosenService;
				v['showType']="host";
				v['group'] = host; 
                v['host'] = host;
                v['name'] = 'zoo_id';
                v['value'] = getZooid(host) ;
                v['type'] = 'string';
                v['text'] = 'zookeeper的标记id'
                
                $scope.vars.push(v);
                console.log($scope.vars)
			}
		}
		
		$("#hostNewServiceModal").modal();
	}
	$scope.setupInstance=function(){
		if( $scope.addInstance.length ==0 && $scope.delInstance.length == 0 ){
			$rootScope.alert("找不到要安装或者卸载的实例");
			return;
		}
		$http({
	        method: 'GET',
	        url: '/adminback/add_del_instance',
	        params:  
        	{
        		"add" : angular.toJson($scope.addInstance),
        		"del" : angular.toJson($scope.delInstance),
        		"vars" : angular.toJson($scope.vars)
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
	    		var warn_msg = response["msg"]
	    		console.log(warn_msg)
	    		warn_msg  = warn_msg.split("\n")
	    		for( index in warn_msg ){
	    			if( warn_msg[index] !=null && warn_msg[index] !=""){
	    				$rootScope.alert(warn_msg[index],"warn");	
	    			}
	    		}
	    		var runningId=response['addRunningId'].concat(response['delRunningId'])
		    	$rootScope.beginProgress(runningId,$scope.initRole);
	    	}
	    	
	    }).error(function(data, status) {
	    	$rootScope.alert("发送add_del_instance请求失败");
	    });
	}
	//组相关的函数
	$scope.readyAddGroup=function(){
		$scope.nowGroup={}
		$scope.nowGroup.group=""
		$scope.nowGroup.edit=false
		$scope.nowGroup.text=""
		$("#hostNewGroupModal").modal();
	}
	$scope.editGroup=function(group){
		$scope.nowGroup={}
		$scope.nowGroup.group=group
		$scope.nowGroup.edit=true
		$scope.nowGroup.text=$scope.groups[group]
		$("#hostNewGroupModal").modal();
	}
	$scope.saveGroup=function(del){
		if( del == null ) del= "";
		$http({
	        method: 'GET',
	        url: '/adminback/save_group',
	        params:  
        	{
        		"group" : $scope.nowGroup.group,
        		"text" : $scope.nowGroup.text,
        		"del" : del  
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	$scope.initGroup()
	    }).error(function(data, status) {
	    	$rootScope.alert("发送save_group请求失败");
	    });
	}
	$scope.readySetupGroup=function(){
		var del=[];
		var add=[];
		
		for(var host in $scope.hostgroups){
			var groupList = $scope.hostgroups[host]['group']
			for(var group in $scope.groups ){
				var oldRea = inArray(groupList,group);
				var newRea = $scope.hostGroupMap[host][group];
				if( oldRea && !newRea ){
					console.log(host+" "+group)
					del.push({"host":host,"group":group});
				}
				if( !oldRea && newRea ){
					console.log(host+" "+group)
					add.push({"host":host,"group":group});
				}
			}
		}
		$scope.addGroup=add;
		
		$scope.delGroup=del;
		$("#hostEditGroupModal").modal();
	}
	$scope.setupGroup=function(){
		if( $scope.addGroup.length==0 && $scope.delGroup==0){
			$rootScope.alert("找不到要修改的组关系");
			return;
		}
		$http({
	        method: 'GET',
	        url: '/adminback/setup_group',
	        params:  
        	{
        		"add" : angular.toJson($scope.addGroup),
        		"del" : angular.toJson($scope.delGroup)
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	$scope.initGroup()
	    }).error(function(data, status) {
	    	$rootScope.alert("发送请求失败");
	    });
	}
	
	$scope.autoFlush = function(){
		$scope.initHost();
		$scope.initRole();
	}
	
	//tab操作和跳转
	$rootScope.menu="admin";
	$rootScope.submenu="host";	
	//注册自动刷新
	$rootScope.registerAutoFlush( "host", $scope.autoFlush)
	
	
	$scope.tab="host";
	
}])
