uhpApp.controller('SettingCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){

  $scope.showValue=function(v){
    if(v && v.name && v.name.length>5 && v.name.slice(-5) == '_pass'){
      return "********";
    }
    return v.value;
  }
	
	$scope.initConf=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/conf_var',
	        params:  { 
	        	"showType" : $scope.showType,
	        	"service" : "",
	        	"group" : "all"
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
	    	$rootScope.alert("发送 conf_var请求失败");
	    });
		
		$http({
	        method: 'GET',
	        url: '/adminback/hosts'
	    }).success(function(response, status, headers, config){
	        $scope.hosts = [];
	        for(var host in response["hosts"]){
	        	$scope.hosts.push(host)
	        }
	    }).error(function(data, status) {
	    	$rootScope.alert("发送hosts请求失败");
	    });
	}
	
	//添加配置
	$scope.addConfVar=function(){
		if ( $scope.showType == "group" ){
			$scope.nowConfVar={"service": "","group": "all","type":"string"};
			$scope.showConfModal();
		}
		else{
			$scope.nowConfVar={"service": "","type":"string"};
			$scope.showConfModal();
		}
	}
	//修改配置
	$scope.editConfVar=function(oneConfVar){
		$scope.nowConfVar=oneConfVar;
		for(var key in oneConfVar){
			$scope.nowConfVar[key]=oneConfVar[key];
		}
		$scope.nowConfVar["host"] = oneConfVar["group"]
		$scope.nowConfVar["service"] = ""
		$scope.nowConfVar["del"] = true;
		$scope.showConfModal()
	}
	$scope.showConfModal=function(){
		$("#settingConfModal").modal('toggle');
	}
	
	//保存配置
	//保存修改删除conf
	$scope.saveConf=function(del){
		if( $scope.nowConfVar.type == "list"){
			$scope.nowConfVar.value = $scope.nowConfVar.value.replace(new RegExp("\n","gm"),",");
		}
		$http({
	        method: 'GET',
	        url: '/adminback/save_conf_var',
	        params:  {
	        	"service" : "",
	        	"showType" : $scope.showType,
	        	"group" :$scope.nowConfVar.group,
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
	    	$rootScope.alert("发送save_global_conf_var请求失败");
	    });
	}
	
	$scope.$watch("showType",function(newValue,oldValue){
		$scope.initConf();
	});
	
	$rootScope.showType = "group"
	$rootScope.menu = "admin";
	$rootScope.submenu = "setting";	
	$scope.initConf();
}]);
