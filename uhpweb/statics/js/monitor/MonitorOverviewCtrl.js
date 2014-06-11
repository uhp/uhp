// 概览
uhpApp.controller('MoniOverviewCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', '$interval', function($scope, $rootScope, $http, $sce, $timeout, $interval){
  MonitorBaseController($scope, $rootScope, $timeout);
 
  var labelColor = ['label-danger','label-warning','label-success'];

  $scope.mapColor = function(v){
    return labelColor[parseInt(v/34)]; 
  }

  $scope.fetchCurrentHealths = function(){
    //$rootScope.myHttp('GET', '/statics/static_data/monitor/fetch_current_healths', 
    $rootScope.myHttp('GET', '/monitorback/fetch_current_healths', 
      {}, 
      function(res){
        $scope.show.healths=res['data'];
      }
    );
  }

  $scope.init = function(){
    $scope.showInfo();
    $scope.fetchCurrentHealths();
    
    // 根据时间触发定时任务，动态刷新当前健康度数据，
    // 当前状态标签被激活 定时事件
    $.each($rootScope.menus.menus, function(i, menu){
      if(menu.name != 'monitor') return true;
      $.each(menu.submenus, function(j, submenu){
        if(submenu.name != 'mOverview') return true;
        $.each(submenu.tabs, function(k,tab){
            if(tab.name != 'mtCurent') return true;
            var stop = null;
            $scope.$watch(function(){return submenu.active+'|'+tab.active;}, 
              function(newValue, oldValue){
                if(newValue == 'active|active' && stop == null){
                  stop = $interval(function(){
                    $scope.fetchCurrentHealths();
                  },60000);
                }else if(newValue != 'active|active' && stop != null){
                  $interval.cancel(stop);
                  stop = null;
                }
              }
            );
            return false;
        });
        return false;
      });
      return false;
    });

    // 监察精度，响应精度选择
    $scope.$watch(function(){return $scope.show.precision;},function(){
      if(!$scope.show.precision) return;
      //$rootScope.myHttp('GET', '/statics/static_data/monitor/fetch_history_healths', 
      $rootScope.myHttp('GET', '/monitorback/fetch_history_healths', 
        {precision:$scope.show.precision}, 
        function(res){
          $scope.show.all_health_history = res['data'];
          xfunc = $scope.default_xfunc;
          angular.forEach($scope.show.all_health_history, function(v, k){
            if(v.type=='single'){ 
              v.x = $.map(v.x, xfunc);
            } else if(v.type == 'multi'){
              $.each(v.group, function(i, m){
                m.x = $.map(m.x, xfunc);
              });
            }
          });
        }
      );
    });

    // 加载最新的告警列表，最多显示前100条, 不需要定时任务
    //$rootScope.myHttp('GET', '/statics/static_data/monitor/fetch_last_alarm_list', 
    //$rootScope.myHttp('GET', '/monitorback/fetch_last_alarm_list', 
    //  {}, 
    //  function(res){
    //    $scope.alarms = res['data'];
    //  }
    //);

	  $scope.$watch(function(){return $scope.nowPage}, function(newValue,oldValue){
	    $scope.query();
	  });
  }

	$scope.query = function(){
    $rootScope.myHttp('GET', '/monitorback/query_alarms', 
    	{
    		"search"  : $scope.alarmSearchText,
    		"orderby" : $scope.orderbyField,
    		"dir"     : $scope.orderDir,
    		"offset"  : ($scope.nowPage - 1) * $scope.limit,
    		"limit"   : $scope.limit
    	},
      function(res){
        $scope.alarms = res['data'];
        console.debug($scope.alarms);
      }
    );
	}
	
  $scope.enterQuery=function(code){
		if( code == 13 ){
			$scope.query()
		}
	}

	$scope.jump=function(wantPage){
    //var wantPage = $(':text[name=wantPage]');
    //var wantPage = wantPage.val();
    //if(!wantPage){ return false; }
    //$scope.wantPage=parseInt(wantPage);
    //console.debug(wantPage);
    wantPage=parseInt(wantPage);
		$scope.nowPage = Math.min(Math.max(wantPage, 1), $scope.alarms.totalPage);
	}

	$scope.alarmSearchText  = "";
	$scope.orderbyField     = "id";
	$scope.orderDir         = "desc";
	$scope.nowPage          = 1;
	$scope.limit            = 50;

	$scope.alarms           = {};
	$scope.alarms.total     = 0;
	$scope.alarms.totalPage = 0;
	$scope.alarms.columns   = [];
	$scope.alarms.rows      = [];

  $scope.init();
}]);
