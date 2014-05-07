
uhpApp.controller('NarCtrl',['$scope','$rootScope','$interval','$http','$location',function($scope,$rootScope,$interval,$http,$location){

	$rootScope.user={}
	$rootScope.menus={} //第一菜单
	$rootScope.narmenu={} //激活的第一菜单
	$rootScope.submenus={} //第二菜单
  $rootScope.menu='' //激活的第一菜单项的name, admin使用
  $rootScope.submenu='' //激活的第二菜单项的name, admin使用
	$rootScope.activedSubMenu={} //激活的第二菜单, monitor使用
  
  //公共函数
  $rootScope.myHttp=function(method, url, params, func){
		$http({
	    method: method,
	    url: url,
	    params: params || {}
	  }).success(function(response, status, headers, config){
      if(response["ret"] != "ok") {
	  	  $rootScope.alert("服务失败:" + response['msg']);
        return false;
      }
      func(response);
	  }).error(function(data, status) {
	  	$rootScope.alert("发送请求失败:" + data + ":" + status);
	  });
  }   
  
  $rootScope.setActiveMenu = function(menu) {
    $rootScope.narmenu = menu;
  }
 
  // 设置监控的ActivedSubMenu的ActiveTab
  $rootScope.setActiveMonMenuTab=function(tabItem){
    menuItem = $rootScope.activedSubMenu;
    if(menuItem.activeTab === tabItem) return;
    if(menuItem.activeTab) menuItem.activeTab.active = '';
    menuItem.activeTab = tabItem;
    tabItem.active = 'active';
  }
  
  // 设置监控的ActivedSubMenu的ActiveTab
  $rootScope.setActiveMonMenuTabByName=function(tabName){
    angular.forEach($rootScope.activedSubMenu.tabs, function(v, k){
      if(v.name == tabName){
        $rootScope.setActiveMonMenuTab(v);
        return false;
      }
    });
  }

  function findAndActiveSubMenu(path){
    if(!path) path = $location.path();
    var submenu = null;
    angular.forEach($rootScope.narmenu.submenus, function(v, k){
      var href = v.href.replace('#', '');
      if(href == path){
        submenu = v;
        return false;
      }
    });
    if(submenu) $rootScope.setActiveSubMenu(submenu);
  }

  // 根据新的URL Path确定ActivedSubMenu
  $rootScope.$on('$locationChangeSuccess', function(){
    menu = $rootScope.narmenu;
    if(menu.name=='monitor'){ //继续深入子目录
      findAndActiveSubMenu();
    }
  });

  $rootScope.setActiveSubMenu = function(menu) {
    angular.forEach($rootScope.narmenu.submenus, function(v, k){
      if(v.active == 'active') v.active = '';
    });
    $rootScope.activedSubMenu = menu;
    menu.active = 'active';

    if(menu && menu.tabs){
      var noActiveTab = true;
      angular.forEach(menu.tabs, function(v, k){
        if(v.active == 'active') {
          noActiveTab = false;
          return false;
        }
      });
      if(noActiveTab) {
        $rootScope.setActiveMonMenuTab(menu.tabs[0]);
      }
    }
  }

	$http({
	  method: 'GET',
	  url: '/adminback/user'
	}).success(function(response, status, headers, config){
	  $rootScope.menus = response["menus"];
    $rootScope.is_manager = response["menus"]["is_manager"];
    $rootScope.is_monitor = response["menus"]["is_monitor"];
    console.log("is_manager:" + $rootScope.is_manager);
    console.log("is_monitor:" + $rootScope.is_monitor);
	  $rootScope.user= response["user"];
	  //$rootScope.submenus = response["menus"]["menus"]["submenus"];
    
    path = $location.path();
    console.log('path1:'+path);
    if(path != null && path.length > 0){
      path = path.replace('/', '');
      $.each($rootScope.menus.menus, function(i, item){
        if(path.slice(0, item.name.length) == item.name){
          $rootScope.narmenu = item;
          if(item.name=='monitor'){ //继续深入子目录
            findAndActiveSubMenu();
          }
          return false;
        }
      });
    }
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
	$rootScope.initAlerts=function(){
		var temp = getCookie("alerts")
		if( temp != null && temp != "" ){
			$rootScope.alerts = angular.fromJson(temp)
		}
		else{
			$rootScope.alerts = []
		}
		if( $rootScope.alerts.length == 0 ){
			$rootScope.alerts.push({"msg": "welcome to uhp !!","type":"info"})
		} 
		setCookie("alerts",angular.toJson($rootScope.alerts),{"expireSeconds":300});
	}
	$rootScope.initAlerts()
	$rootScope.alert=function(msg,type){
    // zhaigy
		if( type == null || type == "" || type == "now" || type == "error" || type == "warn"){
			type = $.scojs_message.TYPE_ERROR;
		} else {
			type = $.scojs_message.TYPE_OK;
    }
    $.scojs_message(msg, type);
		return;
    // ~zhaigy
		var temp = getCookie("alerts")
		if( temp != null && temp != "" ){
			$rootScope.alerts = angular.fromJson(temp)
		}
		if( type == null || type==""){
			type="danger"
		}
		if( type == "now"){
			alert(msg);
		}
		var msgHead = get_now_hms();
		if( type == "danger" ){
			msgHead +=" ERROR ";
		}
		else if( type == "info" ){
			msgHead +=" INFO ";
		}
		else if( type == "warn" ){
			msgHead +=" WARN ";
		}
		else if( type == "welcome" ){
			return
		}
		$rootScope.alerts.unshift({"msg": msgHead+msg,"type":type});
		if($rootScope.alerts.length>10){
			$rootScope.alerts.pop();
		}
		setCookie("alerts",angular.toJson($rootScope.alerts),{"expireSeconds":300});
	}
	$rootScope.closeAlert = function(index) {
		$rootScope.alerts.splice(index, 1);
		//$cookieStore.put("alerts",$rootScope.alerts);
		setCookie("alerts",angular.toJson($rootScope.alerts),{"expireSeconds":300});
	};
	
	$rootScope.showFirst = function(){
		if($rootScope.first !=null && $rootScope.first == false) return
		$rootScope.alert("初次安装请到设置进行必要的配置,星号的配置请留意","warn")
		$rootScope.first = false;
	}

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
	
	//href
	$rootScope.href=function(url){
		window.location.href=url
	}
}])
