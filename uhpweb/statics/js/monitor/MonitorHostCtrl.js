// 机器 Host host
uhpApp.controller('MoniHostCtrl', ['$scope', '$rootScope', '$http', '$sce', '$timeout', '$location', 'anchorSmoothScroll', function($scope, $rootScope, $http, $sce, $timeout, $location, anchorSmoothScroll){
  MonitorBaseController($scope, $rootScope, $timeout, $location, anchorSmoothScroll);
  $scope.groups = ['default','default-ext'];

  // 按钮后，转到HostMetrics展示
  $scope.showHost=function(host_metric){
    $scope.show.host=host_metric.host;
    $rootScope.setActiveMonMenuTabByName('mtHostMetrics');
  }

  // 按钮后，转到HostsMetric展示
  $scope.showMetric=function(host_metric){
    $scope.show.metric=host_metric.metric;
    $rootScope.setActiveMonMenuTabByName('mtHostsMetric');
  }

  $scope.fetchHostCurrentOverview = function(){
    //$rootScope.myHttp('GET', '/statics/static_data/monitor/fetch_host_current_overview', 
    $rootScope.myHttp('GET', '/monitorback/fetch_host_current_overview', 
      {}, 
      function(res){
        $scope.show.hostOverview      = res['hostOverview'];
        $scope.show.loadDist          = [res['loadDist']];
        // data:[{name,x:[],series:[{name:,type:,data:[]}]}]
        $scope.show.all_host_overview = res['data'];
        $scope.show.diskData = res['diskData'];
        if($scope.show.diskData && $scope.show.diskData.length > 0){
          $scope.activeIdx(0, $scope.show.diskData);
        }
      }
    );
  }

  
  $scope.showHostMainMetrics = function(newValue, oldValue, scope){
    console.log('precision:' + scope.show.precision);
    console.log('host:' + scope.show.host);
    if(!scope.show.precision || !scope.show.host) return;
    $rootScope.myHttp('GET', '/monitorback/show_host_main_metrics', 
      {precision:scope.show.precision, host:scope.show.host, groups:scope.groups}, 
      function(res){
        scope.show.host_main_metrics=[];
        angular.forEach(res['data'], function(v, k){
          v.host = scope.show.host;
          xfunc = $scope.default_xfunc;
          v.x = $.map(v.x, xfunc);
          this.push(v);
        }, scope.show.host_main_metrics);
      }
    );
  }

  // 计算分布情况
  $scope.calculateDistribution = function(group_metric){
    var host_metric = group_metric;
    // 计算分布
    var rose_group_metric = {name:host_metric.metric, data:[]};
    
    function rangeLoad(n){
      var H = 10.0;
      var h = n/H;
      var r = parseInt(h * 100);
      if(r<0) return -1;
      if(r==0) return 0;
      if(r<=100) return parseInt((r-1)/25);
      return 4;
    }

    var data = [0,0,0,0,0,0];
    $.each(host_metric.y, function(i,n){
      r = rangeLoad(n);
      r = r+1;
      data[r] = data[r] + 1; 
    });
    var dataNames = ["Down","0-25%","25-50%","50-75%","75-100%","100%+"];
    $.each(data, function(i,n){
      rose_group_metric.data.push({value:n,name:dataNames[i]});
    });
    //过滤掉0值
    rose_group_metric.data = $.map(rose_group_metric.data, function(n){
      return n.value<=0?null:n;
    });
    return rose_group_metric;
  }
  
  $scope.init = function(){
    $scope.showInfo();
    $scope.fetchHostCurrentOverview();
    $scope.$watch(function(){ var v= "main:" + $scope.show.precision +"|"+ $scope.show.host; return v;}, $scope.showHostMainMetrics);
  }

  $scope.init();

}]);
