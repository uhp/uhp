//use base.js
//
var uhpApp = angular.module('uhpApp', ['ngRoute', 'ngAnimate']);
//,'ui.bootstrap'

uhpApp.config(['$routeProvider', "$interpolateProvider", function($routeProvider, $interpolateProvider) {
	$interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
    $routeProvider
    	.when('/user-info',
        {
            controller: 'InfoCtrl',
            templateUrl: '/statics/partials/user/info.html'
        })
        .when('/user-hdfs',
        {
            controller: 'HdfsCtrl',
            templateUrl: '/statics/partials/user/hdfs.html'
        })
        .when('/user-yarn',
        {
            controller: 'YarnCtrl',
            templateUrl: '/statics/partials/user/yarn.html'
        })
        .otherwise({ redirectTo: '/user-hdfs' });
}]);

uhpApp.controller('NarCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$scope.user={}
	$scope.menus={}
	$scope.submenus={}
	$http({
	        method: 'GET',
	        url: '/userback/user'
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
}])

uhpApp.controller('InfoCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$rootScope.submenu="info";	
	
}])
uhpApp.controller('HdfsCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$rootScope.submenu="hdfs";	
	$scope.initQuota=function(){
		$http({
	        method: 'GET',
	        url: '/static/static_data/user/hdfs_quota.json'
	    }).success(function(response, status, headers, config){
	        $scope.quotas = response["quotas"];
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
	}
	$scope.initQuota()
}])
uhpApp.controller('YarnCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$rootScope.submenu="yarn";
	$scope.tab="quota"
	$scope.tabClass=function(tabName,suffix){
		if(suffix==null) suffix="";
		if($scope.tab==tabName) return "active "+suffix;
		else return "";
	}
	$scope.initQuota=function(){
		$scope.tab="quota"
		$http({
	        method: 'GET',
	        url: '/static/static_data/user/yarn_quota.json'
	    }).success(function(response, status, headers, config){
	        $scope.quotas = response["quotas"];
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
	}
	$scope.initQuota()
	$scope.initRunning=function(){
		$scope.tab="running"
	}
	$scope.getRunning=function(){
		$http({
	        method: 'GET',
	        url: '/static/static_data/user/yarn_running.json'
	    }).success(function(response, status, headers, config){
	        $scope.queues = response["queues"];
	        $scope.rmhost = response["rmhost"];
	        $scope.rmport = response["rmport"];
	        $scope.formatApp($scope.queues)
	        $scope.initmr($scope.queues);
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
	}
	$scope.formatApp=function(){
		for(var queue in $scope.queues){
			for(var appid in $scope.queues[queue]){
				$scope.queues[queue][appid]=$scope.formatOneapp($scope.queues[queue][appid])
			}
		}
	}
	$scope.formatElapsedTime=function(elapsedTime){
		if( elapsedTime=="x" ) return elapsedTime;
		var sec = Math.floor(elapsedTime/1000);
		var min = Math.floor(sec/60);
		sec = sec - min*60;
		return min+"m"+sec+"s";
	}
	$scope.formatOneapp=function(info){
		last = info['id'].lastIndexOf("_")
		info['id']=info['id'].substring(last+1)
		info['name']=info['name'].substring(0,100)
		
		last = info['amHostHttpAddress'].lastIndexOf(":")
		info['amHost']=info['amHostHttpAddress'].substring(0,last)
		info['elapsedTime']=$scope.formatElapsedTime(info['elapsedTime'])
		info['progress']=Math.floor(info['progress'])+"%"
		var nowTs=new Date().getTime();
		info['startedTime']=$scope.formatElapsedTime(nowTs-info['startedTime'])
		return info;
	}
	$scope.initmr=function(queues){
		var mr = {};
		for(var queue in queues){
			for(var appid in queues[queue]){
				mr[appid]={}
				mr[appid]['map']={}
				mr[appid]['reduce']={}
				
				mr[appid]['map']['All']='-'
				mr[appid]['map']['Pend']='-'
				mr[appid]['map']['Run']='-'
				mr[appid]['map']['Fail']='-'
				mr[appid]['map']['Kill']='-'
				mr[appid]['map']['Succ']='-'
				mr[appid]['reduce']['All']='-'
				mr[appid]['reduce']['Pend']='-'
				mr[appid]['reduce']['Run']='-'
				mr[appid]['reduce']['Fail']='-'
				mr[appid]['reduce']['Kill']='-'
				mr[appid]['reduce']['Succ']='-'
			}
		}
		$scope.mr=mr;
	}
	//历史查询 接口和yarn_monitor的appsum保持一致
	//applist增加了返回数据
	$scope.initHistory=function(){
		$scope.tab="history"
		$scope.filter={}
		$http({
	        method: 'GET',
	        url: '/static/static_data/user/yarn_appsum.json'
	    }).success(function(response, status, headers, config){
	        $scope.resultRecord = response["resultRecord"];
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
		$http({
	        method: 'GET',
	        url: '/static/static_data/user/yarn_applist.json'
	    }).success(function(response, status, headers, config){
	        $scope.applist = response["applist"];
			$scope.formatAppList()
	        $scope.rmhost = response["rmhost"];
	        $scope.rmport = response["rmport"];
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
		$scope['showBaseInfo']=true
	}
	$scope.choose=function(show){
		if( $scope[show] == null || $scope[show] == false)$scope[show]=true;
		else $scope[show]=false;
	}
	$scope.isActive=function(show){
		if( $scope[show] ) return "active";
		else return "";
	}
	
	$scope.formatGB=function(bytes){
		return (bytes/(1024*1024*1024)).toFixed(2); 
	}
	$scope.formatMB=function(bytes){
		return (bytes/(1024*1024)).toFixed(2); 
	}
	$scope.float1=function(a,b){
		return (a/b*100).toFixed(1); 
	}
	$scope.toSzie=function(bytes){
		var mb = (bytes/(1024*1024*1024)).toFixed(1);
		if( mb < 1024) return mb+"MB";
		else {
			var gb = (mb/1024).toFixed(1);
			if(gb<1024) return gb+"GB";
			else return (gb/1024).toFixed(1)+"TB";
		}
	}
	$scope.formatAppList=function(){
		var tempList = [];
		for(var index in $scope.applist){
			var app = []
			for(var i in $scope.applist[index]){
				var v = $scope.applist[index][i]
				if(i==0){
					app['appid'] = v;
					last = v.lastIndexOf("_");
					app['id'] = v.substring(last+1);
				}
				else if(i==1) app['user'] = v;
				else if(i==2) app['name'] = v;
				else if(i==3) app['queue'] = v;
				else if(i==4) app['startedTime'] = unix_to_datetime(v*1000);
				else if(i==5) app['finishedTime'] = unix_to_datetime(v*1000);	
				else if(i==6) app['state'] = v;
				else if(i==7) app['finalStatus'] = v;
				else if(i==8) app['attemptNumber'] = v;
				
			    else if(i==9)  app['mapsTotal']=v;
			    else if(i==10) app['mapsCompleted']=v;
			    else if(i==11) app['successfulMapAttempts']=v;
			    else if(i==12) app['killedMapAttempts']=v;
			    else if(i==13) app['failedMapAttempts']=v;
			    else if(i==14) app['avgMapTime']=v;

			    else if(i==15) app['reducesTotal']=v;
			    else if(i==16) app['reducesCompleted']=v;
			    else if(i==17) app['successfulReduceAttempts']=v;
			    else if(i==18) app['killedReduceAttempts']=v;
			    else if(i==19) app['failedReduceAttempts']=v;
			    else if(i==20) app['avgReduceTime']=v;

			    else if(i==21) app['fileRead']=$scope.toSzie(v);
			    else if(i==22) app['fileWrite']=$scope.toSzie(v);
			    else if(i==23) app['hdfsRead']=$scope.toSzie(v);
			    else if(i==24) app['hdfsWrite']=$scope.toSzie(v);
				
			}
			tempList.push(app)
		}
		$scope.applist=tempList
	}
}])
