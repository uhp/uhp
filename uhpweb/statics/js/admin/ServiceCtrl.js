

uhpApp.controller('ServiceCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	
	
	$scope.init=function(){
		//初始化service的静态信息
		$http({
	        method: 'GET',
	        url: '/adminback/services_info'
	    }).success(function(response, status, headers, config){
	    	$scope.services = response["services"];
	    	$scope.roleCheckMap = response["role_check_map"];
	    	$scope.activeServices = []
	    	$scope.unactiveServices = []
	    	for(var index in $scope.services){
				var temp = $scope.services[index]
				if(temp['active']) $scope.activeServices.push(temp['name']);
				else $scope.unactiveServices.push(temp['name'])
			}
	    	$scope.hasService = $scope.activeServices.length!=0
	        $scope.nowService =  $scope.activeServices[0];
	    	
	    	if($scope.activeServices.length == 0){
	    		$rootScope.showFirst();
	    	}
	    	
	    }).error(function(data, status) {
	    	$rootScope.alert("发送services_info请求失败");
	    });
	 	//初始化组列表
	 	$http({
	        method: 'GET',
	        url: '/adminback/group_host_list'
	    }).success(function(response, status, headers, config){
	    	$scope.groups = [];
	    	angular.forEach(response["groups"], function(value, key) {
	    		$scope.groups.push(value.name);
		    });
	    	$scope.hosts = [];
	    	angular.forEach(response["hosts"], function(value, key) {
	    		$scope.hosts.push(value.name);
		    });
	    	$scope.nowGroup = $scope.groups[0];
	    	$scope.nowHost = $scope.hosts[0];
	    	$scope.showType = "group";
	    }).error(function(data, status) {
	    	$rootScope.alert("发送group_host_list请求失败");
	    });
	 	
	}
	
	
	$scope.$watch("nowService",function(newValue, oldValue) {
		$scope.updateNowService();
	}) ;
	$scope.$watch("showType",function(newValue,oldValue){
		$scope.initConf();
	});
	$scope.$watch("nowGroup",function(newValue, oldValue) {
		$scope.initConf();
	}) ;
	//*******************************************************************
	//添加服务中的步骤管理
	$scope.lastMove = 3;
	$scope.setupMove = 1;
	$scope.showSetupService=function(){
		if( $scope.hosts.length == 0 ){
			$rootScope.alert("请先添加机器");
			return;
		}
		$http({
	        method: 'GET',
	        url: '/adminback/doing'
	    }).success(function(response, status, headers, config){
	    	$scope.doing = response['doing']
	    	if($scope.doing!=null && $scope.doing.length !=0) $scope.isDoing=true;
	    	else $scope.isDoing=false;
	    	
	    	if($scope.isDoing){
	    		$rootScope.alert("有部分实例正在安装或者卸载,当前不允许修改实例 ");
			}
	    	else{
	    		$scope.setupMove = 1;
	    		$("#serviceSetupModal").modal();
	    		$scope.setupService = undefined;
	    	}
	    	
	    }).error(function(data, status) {
	    	$rootScope.alert("提交group_host_list请求失败");
	    });
		
	}
	$scope.getTemplateUrl=function(setupMove){
		return "/statics/partials/admin/setup/step_"+setupMove+".html";
	}
	$scope.dependenceCheck=function(service){
		for(var index in $scope.services){
			var temp = $scope.services[index];
			if( temp['name'] == service){
				for(var i in temp['dependence']){
					var wantService = temp['dependence'][i];
					if(inArray($scope.unactiveServices,wantService)){
						return true;
					}
				}
			}
		}
		return false;
	}
	$scope.getDependence=function(service){
		for(var index in $scope.services){
			var temp = $scope.services[index];
			if( temp['name'] == service){
				return temp['dependence'].join(",")
			}
		}
		return false;
	}
	$scope.checkAndNextStep=function(){
		if($scope.setupMove==1){
			//获取选择的服务
			//初始化安装的对照表
			var temp = $("input[name='choseService']:checked").val();
			if( temp != null){
				$scope.setupService = temp;
				for(var index in $scope.services){
					if( $scope.services[index]['name'] == $scope.setupService){
						$scope.setupRoles = $scope.services[index]['role'];
						break;
					}
				}
				$scope.setupHostRoleMap=buildMap($scope.hosts,$scope.setupRoles)
			}
			else{
				$rootScope.alert("请选择服务","now");
				return;
			}
		}
		else if( $scope.setupMove == 2 ){
			//计算安装的服务
			if( !$scope.readySetupService() ){
				return
			}
			//检查实例数量
			if( $scope.roleCheckMap != null ){
				roleNum = {}
				for(var index in $scope.addService){
					var temp = $scope.addService[index]
					if( temp['role'] in roleNum )
						roleNum[temp['role']] += 1
					else{
						roleNum[temp['role']] = 1
					}
				}
				console.log(roleNum)
				for(var index in $scope.setupRoles){
					var role = $scope.setupRoles[index]
					var num = 0
					if( role in roleNum ){
						num = roleNum[role];
					}
					if(role in $scope.roleCheckMap ){
						var rule = $scope.roleCheckMap[role]
						if( "max" in rule && num > rule["max"]){
							$rootScope.alert("角色"+role+"的数量必须不大于"+rule["max"],"now");
							return;
						}
						if( "min" in rule && num < rule["min"]){
							$rootScope.alert("角色"+role+"的数量必须不小于"+rule["min"],"now");
							return;
						}
						if( "equal" in rule && num != rule["equal"]){
							$rootScope.alert("角色"+role+"的数量必须等于"+rule["equal"],"now");
							return;
						}
					}
				}
			}
		}
		else if($scope.setupMove==3){
			//TODO
		}
		$scope.setupMove=$scope.setupMove+1;	
	}
	$scope.readySetupService=function(){
		var add=[];
		for(var host in $scope.setupHostRoleMap){
			for(var role in $scope.setupHostRoleMap[host]){
				if( $scope.setupHostRoleMap[host][role] ){
					add.push({"host":host,"role":role});
				}
			}
		}
		$scope.addService=add;
		if($scope.addService.length==0){
			$rootScope.alert("请选择角色","now");
			return false;
		}
		
		//添加特殊变量
		$scope.vars=[]
		if($scope.setupService=="zookeeper"){
			for(var index in $scope.addService){
				var host = $scope.addService[index]['host'];
				
				var v={}
				v['service']=$scope.setupService;
				v['showType']="host";
				v['group'] = host; 
                v['host'] = host;
                v['name'] = 'zoo_id';
                v['value'] = getZooid(host) ;
                v['type'] = 'string';
                v['text'] = 'zookeeper的标记id'
                
                $scope.vars.push(v);
			}
		}
		
		return true;
	}
	$scope.sendSetupService=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/add_service',
	        params:  
        	{
	        	"service" : $scope.setupService,
        		"add" : angular.toJson($scope.addService),
        		"vars" : angular.toJson($scope.vars)
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 信息:"+response["msg"]);
	        }
	    	else{
	    		var warn_msg = response["msg"]
//	    		console.log(warn_msg)
	    		warn_msg  = warn_msg.split("\n")
	    		for( index in warn_msg ){
	    			$rootScope.alert(warn_msg[index],"warn");	
	    		}
		    	var runningId=response['addRunningId']
		    	$rootScope.beginProgress(runningId,$scope.init);
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("提交add_service请求失败");
	    });
	}
	$scope.readyDelService=function(){
		//TODO 加入删除服务前的检查
		$http({
	        method: 'GET',
	        url: '/adminback/can_del_service',
	        params:  {"service" : $scope.nowService}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("不能删除服务 信息:"+response["msg"]);
	        }
	    	else{
	    		$("#delServiceModal").modal()	
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("提交can_del_service请求失败");
	    });
	}
	$scope.sendDelService=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/del_service',
	        params:  {"service" : $scope.nowService}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	$scope.init()
	    }).error(function(data, status) {
	    	$rootScope.alert("提交 del_service 请求失败");
	    });
	}
	//**************************************************
	//修改或者选择service的初始化
	$scope.updateNowService=function(){
		for(var index in $scope.services ){
			var ser=$scope.services[index];
	        if(ser.name == $scope.nowService){
        		$scope.actions = ser.actions;
        		$scope.instanceActions = ser.instanceActions;
        		$scope.urls = ser.urls;
        		if(ser.urls.length!==0){
        			$scope.hasurl=true;
        		}
        		else{
        			$scope.hasurl=false;
        		}
        		break;
        	}
        }
		//初始化instance
		$scope.initInstance();
		//初始化confvar
		$scope.initConf();
		$scope.chosenInstance={};
	}
	
	$scope.initInstance=function(){
		if( $scope.nowService == null || $scope.nowService==""){
			$scope.instances = [];
			$scope.summary = "";
			return;
		}
		$http({
	        method: 'GET',
	        url: '/adminback/service_info',
	        params:  { "service" : $scope.nowService }
	    }).success(function(response, status, headers, config){
	        $scope.summary = response['summary'];
	        $scope.instances = response['instances'];
	        //填充选择项
			$scope.initChosenInstance();
	    }).error(function(data, status) {
	    	$rootScope.alert("提交service_info请求失败");
	    });
	}
	$scope.showInstanceMsg=function(instance){
		$scope.showInstance = instance
		$("#showInstanceMsgModal").modal()
	}
	
//	$scope.getSummaryIconClass=function(nowHealth){
//		return $scope.iconMap[nowHealth]['class'];
//		return ' class="fa fa-circle fa-2" syle="color:green ' ;
//		if(health=="unknow"){
//			return "fa fa-circle fa-2";
//		}
//		else if(health=="healthy"){
//			return "icon-ok";
//		}
//		else if(health=="unhealthy"){
//			return "icon-remove-circle";
//		}
//		else if(health=="down"){
//			return "icon-remove"
//		}
//	}
	$scope.initChosenInstance=function(){
		var nowCi = $scope.chosenInstance
		$scope.chosenInstance = {}
		for(var index in $scope.instances){
			var temp = $scope.instances[index]
			if( temp['name'] in nowCi ){
				$scope.chosenInstance[temp['name']] = nowCi[temp['name']];
			}
			else{
				$scope.chosenInstance[temp['name']] = false;
			}
		}
		if( $scope.chosenAllInstance == null){
			$scope.chosenAllInstance=false
		}
	}
	
	$scope.initConf=function(){
		if( $scope.nowService == null || $scope.nowGroup == null || $scope.showType == null ){
			return;
		}
		$http({
	        method: 'GET',
	        url: '/adminback/conf_var',
	        params:  { 
	        	"service" : $scope.nowService ,
	        	"group": $scope.nowGroup,
	        	"showType" : $scope.showType
	        }
	    }).success(function(response, status, headers, config){
	        $scope.confVar=response["conf"];
	        //将所有的list的逗号转换为\n
	        angular.forEach($scope.confVar, function(value, key) {
		        if( value.type=="list" ) {
		        	value.value = value.value.replace(new RegExp(",","gm"),"\n");
		        }
		    });
	    }).error(function(data, status) {
	    	$rootScope.alert("提交conf_var请求失败");
	    });
	}
	
	$scope.serviceClass=function(serviceName){
		if($scope.nowService==serviceName) return "active-li-a";
		else return "";
	}
	$scope.changeService=function(serviceName){
		$scope.nowService=serviceName;
	}
	
	$scope.tabClass=function(tabName,suffix){
		if(suffix==null) suffix="";
		if($scope.tab==tabName) return "active "+suffix;
		else return "";
	}
	
	$scope.getInstanceList=function(){
		var ret = []
		if( $scope.instances!=null && $scope.chosenInstance!=null){
			for( var name in $scope.chosenInstance){
				if( $scope.chosenInstance[name] ){
					ret.push(name)
				}
			}
		}
		return ret.join("\n");
	}
	//提交action
	$scope.getActionObject=function(){
		if( $scope.actionType =="service" ){
			return $scope.nowService;
		}
		else{
			return "以下机器";
		}
	}
	$scope.readySendServiceAction=function(action,display){
		//拦截特殊的服务操作
//		if( $scope.nowService=="yarn" && action=="moverm"){
//			$scope.infoTargetRM = false;
//			$scope.steps = ["在目标机器上安装ResourceManager","关闭原来的ResourceManager",
//			"修改数据库中ResourceManager的位置","启动新的ResourceManager","重启所有的NodeManager"];
//			console.log($scope.steps)
//			$scope.dostep = []
//			for(var index in $scope.steps){
//				$scope.dostep[index]=true
//			}
//			$("#moveRmModal").modal()
//		}
//		else{
		$scope.todoAction = action;
		$scope.todoDisplay = display;
		$scope.actionType = "service";
		$scope.instanceList = "";
		$("#serviceActionModal").modal();	
	}
	//实例全选
	$scope.$watch("chosenAllInstance",function(newValue,oldValue){
		for(var name in $scope.chosenInstance){
			$scope.chosenInstance[name]=newValue
		}
	})
	$scope.readySendInstanceAction=function(action){
		$scope.todoAction = action;
		$scope.actionType = "instance";
		$scope.instanceList = $scope.getInstanceList();
		if( $scope.InstanceList == "" ){
			$rootScope.alert("请选择实例");
		}
		else{
			$("#serviceActionModal").modal();
		}
	}
	$scope.sendAction=function(action){
		$http({
	        method: 'GET',
	        url: '/adminback/send_action',
	        params:  
	        	{
	        		"service" : $scope.nowService,
	        		"taskName" : $scope.todoAction,
	        		"actionType" : $scope.actionType,
	        		"instances" : $scope.instanceList.replace(new RegExp("\n","gm"),",")
	        	}
	    }).success(function(response, status, headers, config){
	        if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	        else{
	        	var warn_msg = response["msg"]
//	    		console.log(warn_msg)
	    		warn_msg  = warn_msg.split("\n")
	    		for( index in warn_msg ){
	    			$rootScope.alert(warn_msg[index],"warn");	
	    		}
	        	window.location.href="#/admin-task"
	        	//$scope.initInstance();
	        }
	    }).error(function(data, status) {
	    	$rootScope.alert("发送send_action请求失败");
	    });
	}
	//*******************************以下是配置相关
	//展示conf
	$scope.showConfTitle=function(){
		if($scope.showType=="group"){
			return "配置组";
		}
		else{
			return "机器名称";
		}
	}
	//添加config
	$scope.addConfVar=function(){
		if($scope.showType=="group"){
			$scope.nowConfVar={"service":$scope.nowService,"group": $scope.nowGroup,"type":"string"};
		}
		else{
			$scope.nowConfVar={"service":$scope.nowService,"type":"string"};
		}
		$scope.showConfModal();
	}
	//修改config
	$scope.editConfVar=function(oneConfVar){
		$scope.nowConfVar=oneConfVar;
		for(var key in oneConfVar){
			$scope.nowConfVar[key]=oneConfVar[key];
		}
		$scope.nowConfVar["host"] = oneConfVar['group']
		$scope.nowConfVar["service"] = $scope.nowService
		$scope.nowConfVar["del"] = true;
		$scope.showConfModal();
	}
	$scope.showConfModal=function(){
		$("#serviceConfModal").modal();
	}
	//保存修改删除conf
	$scope.saveConf=function(del){
		if( $scope.nowConfVar.type == "list"){
			$scope.nowConfVar.value = $scope.nowConfVar.value.replace(new RegExp("\n","gm"),",");
		}
		$http({
	        method: 'GET',
	        url: '/adminback/save_conf_var',
	        params:  
	        	{
	        		"service" : $scope.nowService,
	        		"showType" : $scope.showType,
	        		"group" : $scope.nowConfVar.group,
	        		"host" : $scope.nowConfVar.host,
	        		"name" : $scope.nowConfVar.name,
	        		"value" : $scope.nowConfVar.value,
	        		"type" : $scope.nowConfVar.type,
	        		"text" : $scope.nowConfVar.text,
	        		"del" : del
	        	}
	    }).success(function(response, status, headers, config){
	        if(response["ret"]=="ok"){
	        	$scope.initConf();
	        }
	        else{
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	        
	    }).error(function(data, status) {
	    	$rootScope.alert("发送save_conf_var请求失败");
	    });
	}
	
	$scope.iconMap={
			"unknow":{"class":"fa fa-circle-o fa-lg","style":"color:rgb(52, 89, 209)"},	
			"healthy":{"class":"fa fa-circle fa-lg","style":"color:rgb(56, 173, 26)"},	
			"unhealthy":{"class":"fa fa-times-circle-o fa-lg","style":"color:rgb(223, 65, 65)"},	
			"down":{"class":"fa fa-circle fa-lg","style":"color:rgb(223, 65, 65)"},	
			
			"start":{"class":"fa fa-play fa-lg","style":"color:rgb(78, 65, 223)"},	
			"stop":{"class":"fa fa-minus fa-lg","style":"color:rgb(78, 65, 223)"},	
			"setup":{"class":"fa fa-refresh fa-lg","style":"color:rgb(78, 65, 223)"},
			"removing":{"class":"fa fa-refresh fa-lg","style":"color:rgb(78, 65, 223)"}
		}
	
	$rootScope.menu="admin";
	$rootScope.submenu="service";
	//注册自动刷新
	$rootScope.registerAutoFlush( "service", $scope.initInstance)
	$scope.init();
	//tab操作和跳转
	$scope.tab="info";
}])
