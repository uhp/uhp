uhpApp.controller('TaskCtrl',['$scope','$rootScope','$interval','$http',function($scope,$rootScope,$interval,$http){
	$scope.orderbyField = "id";
	$scope.orderDir = "desc";
	$scope.nowPage = 1 ;
	$scope.limit = 50;
	$scope.totalTask = 0;
	$scope.nowTask={};
	$scope.$watch("nowPage",function(newValue,oldValue){
		if( newValue < 1 ) newValue=1;
		else if (newValue > $scope.totalPage) newValue=$scope.totalPage;
		else{
			$scope.query();
		}
	});
	$scope.jump=function(){
		if( $scope.wantPage <1 )$scope.wantPage = 1;
		else if ($scope.wantPage > $scope.totalPage) $scope.wantPage=$scope.totalPage;
		$scope.nowPage=$scope.wantPage;
	}
	$scope.isDisable=function(button){
		if( button=="pre" && $scope.nowPage == 1) return "disabled";
		if( button=="next" && $scope.nowPage == $scope.totalPage) return "disabled";
		return " ";
	}
	$scope.getIconClass=function(name){
		if( $scope.orderbyField == name){
			if( $scope.orderDir=="asc" ){
				return "icon-arrow-up";
			}
			else{
				return "icon-arrow-down";
			}
		}
		else return "icon-minus";
	}
	$scope.changeOrderBy=function(name){
		if( $scope.orderbyField == name){
			if( $scope.orderDir =="asc" ){
				$scope.orderDir = "desc";
			}
			else{
				$scope.orderDir = "asc";
			}
		}
		else{
			$scope.orderbyField = name;
		}
		$scope.query();
	}
	$scope.enterQuery=function(code){
		if( code == 13 ){
			$scope.query()
		}
	}
	$scope.query=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/tasks',
	        params:  
        	{
        		"search" : $scope.taskSearchText,
        		"orderby" : $scope.orderbyField,
        		"dir" : $scope.orderDir,
        		"offset" : ($scope.nowPage-1)*$scope.limit,
        		"limit" : $scope.limit
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	$scope.tasks=response["tasks"];
	    	$scope.totalTask =response["totalTask"];
	    	$scope.totalPage = Math.floor(($scope.totalTask-1)/$scope.limit)+1;
	    }).error(function(data, status) {
	    	$rootScope.alert("发送tasks请求失败");
	    });
	}
	
	$scope.showTaskDetail=function(taskid){
		$http({
	        method: 'GET',
	        url: '/adminback/task_detail',
	        params:  {"taskid" : taskid}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
		    	$scope.nowTask=response["task"];
		    	//$scope.nowTask['msg']=formatJson($scope.nowTask['msg'],false)
		    	$("#taskDetailModal").modal();
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送task_detail请求失败");
	    });
	}
	$scope.killTask=function(taskid){
		$http({
	        method: 'GET',
	        url: '/adminback/kill_task',
	        params:  {"taskid" : taskid}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
		    	$rootScope.alert("已经成功发送 kill命令","info");
		    	$scope.query()
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送kill_task请求失败");
	    });
	}
	$scope.canRerun=function(task){
		if( task.service == "prepare" ){
			return true
		}
		else{
			return false;
		}
	}
	$scope.rerunTask=function(taskid){
		$http({
	        method: 'GET',
	        url: '/adminback/rerun_task',
	        params:  {"taskid" : taskid}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
		    	$rootScope.alert("已经重新提交,新的任务id是"+response['taskid'],"info");
		    	$scope.query()
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送rerun_task请求失败");
	    });
	}
	$scope.resultIconMap={
		"unfinish":{"class":"fa fa-question-circle fa-lg","style":"color:rgb(52, 89, 209)"},	
		"failed":{"class":"fa fa-times-circle-o fa-lg","style":"color:rgb(223, 65, 65)"},
		"timeout":{"class":"fa fa-circle fa-lg","style":"color:rgb(223, 65, 65)"},		
		"killed":{"class":"fa fa-pause fa-lg","style":"color:rgb(223, 65, 65)"},	
		"success":{"class":"fa fa-check-circle-o fa-lg","style":"color:rgb(56, 173, 26)"}
	}
	//tab操作和跳转
	$rootScope.menu="admin";
	$rootScope.submenu="task";	
	//注册自动刷新
	$rootScope.registerAutoFlush( "task", $scope.query)
	$scope.query();
}]);
