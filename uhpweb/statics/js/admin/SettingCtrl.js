uhpApp.controller('SettingCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$rootScope.menu="admin";
	$rootScope.submenu="setting";	
	$scope.initConf=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/global_conf_var',
	    }).success(function(response, status, headers, config){
	        $scope.confVar=response["conf"];
	        //将所有的list的逗号转换为\n
	        angular.forEach($scope.confVar, function(value, key) {
		        if( value.type=="list" ) {
		        	value.value = value.value.replace(new RegExp(",","gm"),"\n");
		        }
		    });
	    }).error(function(data, status) {
	    	$rootScope.alert("发送 global_conf_var请求失败");
	    });
	}
	$scope.initConf();
	//添加配置
	$scope.addConfVar=function(){
		$scope.nowConfVar={"service": "","group": "all","type":"string"};
		$scope.showConfModal();
	}
	//修改配置
	$scope.editConfVar=function(oneConfVar){
		$scope.nowConfVar=oneConfVar;
		for(var key in oneConfVar){
			$scope.nowConfVar[key]=oneConfVar[key];
		}
		$scope.nowConfVar["host"] = "all"
		$scope.nowConfVar["service"] = ""
		$scope.nowConfVar["del"] = true;
		$scope.showConfModal();
	}
	$scope.showConfModal=function(){
		$("#settingConfModal").modal();
	}
	//保存配置
	//保存修改删除conf
	$scope.saveConf=function(del){
		if( $scope.nowConfVar.type == "list"){
			$scope.nowConfVar.value = $scope.nowConfVar.value.replace(new RegExp("\n","gm"),",");
		}
		$http({
	        method: 'GET',
	        url: '/adminback/save_global_conf_var',
	        params:  {
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
	    	$rootScope.alert("发送save_global_conf_var请求失败");
	    });
	}
}]);