
uhpApp.controller('NarCtrl',['$scope','$rootScope','$interval','$http',function($scope,$rootScope,$interval,$http){
	$scope.user={}
	$scope.menus={}
	$scope.submenus={}
	$http({
	        method: 'GET',
	        url: '/adminback/user'
	    }).success(function(response, status, headers, config){
	        $scope.menus = response["menus"];
	        $scope.user= response["user"];
	        //TODO 判断深度连接使用adminmenus或者usermenus
	        $scope.submenus = response["menus"]["submenus"];
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
	$rootScope.isActiveSubmenu=function(submenu){
		if($rootScope.submenu == submenu) return "active";
		else return "";
	}
	//轮询指定的执行任务，获取进度。在任务地方想调用进度条。
	//调用$rootScope.beginProgress即可传入任务id的数组
	$rootScope.beginProgress=function(id,callback){
		$rootScope.runningId = id;
		$("#progressModal").modal();
		$rootScope.progress=0;
		$rootScope.progressMessage="";
		$rootScope.progressCallback=callback;
		$rootScope.close=false;
		$rootScope.updateProgress();
		$rootScope.success=false;
		stop = $interval($rootScope.updateProgress, 1000);
	}
	$rootScope.updateProgress=function(){
		if( $rootScope.close ) return;
//		console.log(angular.toJson($rootScope.runningId))
		$http({
	        method: 'GET',
	        url: '/adminback/query_progress',
	        params:  { "id" : angular.toJson($rootScope.runningId) }
	    }).success(function(response, status, headers, config){
	    	$rootScope.progressMessage = response['progressMsg'];
	    	if( $rootScope.progress != response['progress'] ){
	    		$rootScope.progress = response['progress'];
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送query_progress请求失败");
	        $rootScope.closeProgress()
	    });
		
		if( $rootScope.progress == 100 ){
			$rootScope.successProgress();
		}
	}
	$rootScope.successProgress=function(){
		if (angular.isDefined(stop)) {
	      $interval.cancel(stop);
	      stop = undefined;
	    }
		$rootScope.success=true;
		if( $rootScope.progressCallback !=null ){
			$rootScope.progressCallback();
		}
	}
	$rootScope.closeProgress=function(){
		if (angular.isDefined(stop)) {
	      $interval.cancel(stop);
	      stop = undefined;
	    }
		$("#progressModal").modal('hide');
		if( $rootScope.progressCallback !=null ){
			$rootScope.progressCallback();
		}
	}
	$rootScope.alerts=[]
	$rootScope.alert=function(msg,type){
		if( type==null || type==""){
			type="danger"
		}
		$rootScope.alerts.push({"msg": msg,"type":type});
		if($rootScope.alerts.length>3){
			$rootScope.alerts.splice(0, 1);
		}
	}
	$rootScope.closeAlert = function(index) {
		$rootScope.alerts.splice(index, 1);
	};
	
	$rootScope.showFirst = function(){
		if($rootScope.first !=null && $rootScope.first == false) return
		$rootScope.alert("初次安装请到设置进行必要的配置,星号的配置请留意","warn")
		$rootScope.first = false;
	}
	$rootScope.alert("welcome to uhp !!","info"); 
	//自动刷新,各个ctrl通过registerAutoFlush注册要自动刷新的函数
	//autoFlush会自动根据submenus名字选择自动刷新的函数并调用
	$rootScope.autoFlushMap = {}
	$rootScope.registerAutoFlush = function(submenu,initFun){
		$rootScope.autoFlushMap[submenu] = initFun;
	}
	$rootScope.autoFlush = function(){
		var initFun = $rootScope.autoFlushMap[$rootScope.submenu]
		if( initFun != null){
			initFun()
		}
	}
	$rootScope.beginAutoFlush = function(){
		stop = $interval($rootScope.autoFlush, 5000);
	}
	$rootScope.beginAutoFlush()
}])