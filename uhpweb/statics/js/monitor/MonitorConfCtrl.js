// 配置 Conf
uhpApp.controller('MoniConfCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
  
  $scope.$watch(function(){return $rootScope.activedSubMenu.activeTab;}, function(newValue, oldValue){
    tabItem = newValue;
    if(tabItem.func) {
      try {
        eval(tabItem.func);
      } catch (err){
        $rootScope.alert("eval " + tabItem.func + " error:" + err.message);
      }
    }
  });

  $scope.query=function(is_refresh){
		if( $scope.sql==null || $scope.sql=="") return;
		$http({
	    method: 'POST',
	    url: '/adminback/manual_query',
	    params:  {
	    	"sql" : $scope.sql
    	}
	  }).success(function(response, status, headers, config){
	  	if(response["ret"]!="ok"){
	      	$rootScope.alert("提交失败 ("+response["msg"]+")");
          return;
	    }
      $scope.column = response['column']
			$scope.data = response['data'];
	  }).error(function(data, status) {
	  	$rootScope.alert("发送manual_query请求失败");
	  });
	}

  function query_global_variate() {
    $scope.sql_table = "monitor_assist";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }

  function query_monitor_metric() {
    $scope.sql_table = "monitor_metric";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }

  function query_monitor_group() {
    $scope.sql_table = "monitor_group";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }

  function query_monitor_host() {
    $scope.sql_table = "monitor_host";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }
  
  function query_alarm() {
    $scope.sql_table = "alarm";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }
  
  function query_alarm_autofix() {
    $scope.sql_table = "alarm_autofix";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }

  function query_alarm_assist() {
    $scope.sql_table = "alarm_assist";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }

  $scope.add_table_record=function(){
    $scope.new_record = {};
    $scope.recordAction="insert";
		$("#monitorConfModal").modal();
  }
  
  $scope.ready_edit_record=function(record){
    $scope.recordAction="update";
    $scope.new_record={};
    $.each($scope.column, function(i,n){
      $scope.new_record[n]=record[i];
    });
		$("#monitorConfModal").modal();
  }

  function make_sql(method, table, values){
    var sql="";
    var opts = {autoQuoteFieldNames: true, autoQuoteTableNames: true};
    if(method == 'insert'){
      sql=squel.insert(opts).into(table).setFields(values).toString();
    } else if (method == "delete"){
      sql=squel.delete(opts).from(table).where("id="+values['id']).limit(1).toString();
    } else if (method == "update") {
      sql=squel.update(opts).table(table).setFields(values).where("id="+values['id']).limit(1).toString();
    }
    return sql;
  }

  $scope.dealRecord=function(record){
		if(!record) return;
    var sql = make_sql($scope.recordAction, $scope.sql_table, $scope.new_record);
    if(!sql) return;
		$http({
	    method: 'POST',
	    url: '/adminback/manual_execute',
	    params:  { sql : sql }
	  }).success(function(response, status, headers, config){
	  	if(response["ret"]!="ok"){
	      	$rootScope.alert("提交失败 ("+response["msg"]+")");
          return;
	    }
      // 刷表格
      $scope.query(true);
	  }).error(function(data, status) {
	  	$rootScope.alert("发送manual_insert请求失败");
	  });
  }

  $scope.save_new_record=function(){
    $scope.dealRecord($scope.new_record)
  }

  $scope.delete_record=function(idx, record){
    var update_record = {id:record[0]};
    //for(i in $scope.column){
    //  update_record[$scope.column[i]] = record[i];
    //}
    var sql = make_sql("delete", $scope.sql_table, update_record);
		$http({
	    method: 'GET',
	    url: '/adminback/manual_execute',
	    params:  { sql : sql }
	  }).success(function(response, status, headers, config){
	  	if(response["ret"]!="ok"){
	      	$rootScope.alert("提交失败 ("+response["msg"]+")");
          return;
	    }
      $scope.data.splice(idx, 1);
      record=null;
	  }).error(function(data, status) {
	  	$rootScope.alert("发送manual delete请求失败");
	  });
  }

  $scope.new_record = {};

}]);
