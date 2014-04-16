var cs = angular.module('cs', []);

cs.controller('NarCtrl', ['$scope', '$rootScope', '$interval', '$http',
    function ($scope, $rootScope, $interval, $http) {
        menu = [{'name':'机器', display:'机器', 'href':'#hosts',   'active':''},
                {'name':'管理', display:'管理', 'href':'/admin',   'active':''},
                {'name':'监控', display:'监控', 'href':'#monitor', 'active':''}];
        $scope.submenus          = menu;
        $scope.activeItem        = menu[0];
        $scope.activeItem.active = 'active';
        $scope.active = function(item){
            if(item == $scope.activeItem) return false;
            $scope.activeItem.active='';
            item.active = 'active';
            $scope.activeItem = item;
        };  
        $http({ method: 'GET', 
            url: '/adminback/user'
        }).success(function(response, status, headers, config){
            $scope.user= response["user"];
        }).error(function(data, status) {
            $rootScope.alert(status);
        });
        
        $rootScope.alerts = [] 
        $rootScope.alert=function(msg, type){
          	if( type == null || type==""){
          		  type="danger"
          	}
          	var msgHead = get_now_hms();
          	if( type == "danger" ){
          		msgHead +=" ERROR ";
          	} else if( type == "info" ){
          		msgHead +=" INFO ";
          	} else if( type == "warn" ){
          		msgHead +=" WARN ";
          	}
          	$rootScope.alerts.unshift({"msg": msgHead+msg, "type": type});
          	if($rootScope.alerts.length>10){
          		$rootScope.alerts.pop();
          	}
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
    } // ~func
]);

cs.controller('HostsCtrl', ['$scope','$rootScope','$http', 
    function($scope,$rootScope,$http){

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
	      	  $rootScope.alert("发送hosts请求失败:" + status);
	      });
	  }

    // 选择过滤机器
    $scope.initChosenHost=function(){
	  	var temp = $scope.chosenHost;
	  	$scope.chosenHost={}
	  	for(var host in $scope.hosts){
	  		if( temp!= null && host in temp ){
	  			$scope.chosenHost[host] = temp[host];
	  		} else {
	  			$scope.chosenHost[host] = false;
	  		}
	  	}
	  	if( $scope.chosenAllHost == null ){
	  		$scope.chosenAllHost = false
	  	}
	  }

	  $scope.filterHostBySearchInfo=function(hosts, search){
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
        var check_items={'机器':$scope.nowHost.hosts,
          '用户':$scope.nowHost.user,
          '端口':$scope.nowHost.port,
          '密码':$scope.nowHost.passwd,
          'SUDO密码':$scope.nowHost.sudopasswd};
        for( x in check_items ) {
          if(!check_items[x]) {
  	  		  $rootScope.alert(x+"不能为空");
            return;
          }
        }
  	  	//if( $scope.nowHost.hosts==null ){
  	  	//	  $rootScope.alert("机器不能为空");
        //    return;
  	  	//}
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
  	        } else {
  	      		  $rootScope.beginProgress(response["runningId"],$scope.initHost);
  	      	}
  	    }).error(function(data, status) {
  	    	  $rootScope.alert("发送add_host请求失败");
  	    });
  	}

	  //全选chosenAll
	  $scope.$watch("chosenAllHost",function(newValue,oldValue){
	  	for(var host in $scope.chosenHost){
	  		$scope.chosenHost[host] = newValue;
	  	}
	  })

    // 删除
	  $scope.readyDelHost=function(){
	  	$scope.chosenHostStr=$scope.getChosenHostStr();
	  	if( $scope.chosenHostStr == "" ){
	  		$rootScope.alert("请选择机器","warn")
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

    $scope.initHost();
}])

var uhpApp = angular.module('uhpApp', ['ngRoute', 
    'cs', 'ngAnimate', 'ui.bootstrap']);

uhpApp.config(['$routeProvider', 
        "$interpolateProvider", 
        '$rootScopeProvider', 
        function($routeProvider, 
            $interpolateProvider,
            $rootScopeProvider) {

            $interpolateProvider.startSymbol('[[');
            $interpolateProvider.endSymbol(']]');

            $routeProvider.when('/monitor', {
                controller: 'MonitorCtrl',
                templateUrl: '/statics/partials/monitor/monitor.html'
            }).when('/hosts', {
                controller: 'HostsCtrl',
                templateUrl: '/statics/partials/monitor/host.html'
            }).otherwise({ 
                redirectTo: '/hosts' 
            });

}]);

