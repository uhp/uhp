


uhpApp.controller('ManualCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$rootScope.menu="admin";
	$rootScope.submenu="manual";	

	$scope.init=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/manual_metadata',
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
		    	$scope.table = response['table']
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送manual_metadata请求失败");
	    });
	}
	$scope.init()
	$scope.$watch("nowTable",function(newValue,oldValue){
		if( newValue != null && newValue !=""){
			$scope.sql = "select * from `"+newValue+"` limit 50";
			$scope.primaryStr = $scope.table[newValue]['primary'].join(",")
			$scope.columnStr = $scope.table[newValue]['column'].join(",")
			$scope.query();
		}
		else{
			$scope.sql = "";
			$scope.primaryStr = ""
			$scope.columnStr = ""	
		}
	});
	$scope.query=function(){
		if( $scope.sql==null || $scope.sql==""){
			return;
		}
		$http({
	        method: 'GET',
	        url: '/adminback/manual_query',
	        params:  {
	        	"sql" : $scope.sql
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	else{
	    		$scope.column = response['column']
		    	$scope.data = response['data']
	    	}
	    }).error(function(data, status) {
	    	$rootScope.alert("发送manual_query请求失败");
	    });
	}
	$scope.edit=function(record){
		$scope.chosenRecord = record;
		$scope.reset()
		$("#editRecordModal").modal();
	}
	$scope.reset=function(){
		$scope.nowRecord={}
		for(var index in $scope.column){
			var col = $scope.column[index];
			var value = $scope.chosenRecord[index];
			$scope.nowRecord[col]=value;
		}
	}
	$scope.isPrimary=function(col){
		if(inArray($scope.table[$scope.nowTable]['primary'],col)) return true;
		else return false;
	}
	$scope.getPrimaryWhere=function(){
		var where = []
		for(var index in $scope.table[$scope.nowTable]['primary']){
			var col = $scope.table[$scope.nowTable]['primary'][index]
			where.push("`"+col+"`='"+$scope.nowRecord[col]+"'")
		}
		var ret = where.join(" and ")
		return ret;
	}
	$scope.saveRecord=function(){
		var where = $scope.getPrimaryWhere();
		var set=[]
		for(var index in $scope.table[$scope.nowTable]['column']){
			var col = $scope.table[$scope.nowTable]['column'][index]
			if( $scope.nowRecord[col] != $scope.chosenRecord[col] ){
				set.push("`"+col+"`='"+$scope.nowRecord[col]+"'")
			}
		}
		var setEx = set.join(" , ")
		var updateSql = "update `"+$scope.nowTable+"` set "+setEx+" where "+where;
		console.log(updateSql)
		$scope.execute(updateSql)
	}
	$scope.deleteRecord=function(){
		var where = $scope.getPrimaryWhere();
		var deleteSql = "delete from `"+$scope.nowTable+"` where "+where;
		console.log(deleteSql)
		$scope.execute(deleteSql)
	}
	$scope.execute=function(sql){
		$http({
	        method: 'GET',
	        url: '/adminback/manual_execute',
	        params:  {
	        	"sql" : sql
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]!="ok"){
	        	$rootScope.alert("提交失败 ("+response["msg"]+")");
	        }
	    	$scope.query();
	    }).error(function(data, status) {
	    	$rootScope.alert("发送manual_execute请求失败");
	    });
	}
}]);