// 服务 Service
uhpApp.controller('MoniServiceCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', '$location', 'anchorSmoothScroll', function($scope, $rootScope, $http, $sce, $timeout, $location, anchorSmoothScroll){
  MonitorBaseController($scope, $rootScope, $timeout, $location, anchorSmoothScroll);
  $scope.groups = ['hadoop-dfs-namenode','hadoop-dfs-datanode','hadoop-dfs-datanode',
    'hadoop-mapred', 'hadoop-yarn-nodemanager',
    'hbase-master', 'hbase-regionserver'];

  // services
  $scope.init=function(){
    $scope.showInfo();

    //show.services_metrics = [{ name:,metrics:[{name:,display:,value:}] } ]
    $rootScope.myHttp('GET', '/monitorback/services_metrics2', 
      {}, 
      function(res){
        // [{name:,hosts:[{host:$host, info:[{name:,value:,unit:,}]}]}] 
        $scope.show.services_metrics=res['data'];
        if($scope.show.services_metrics){
          $.each($scope.show.services_metrics, function(k, v){
            if(v.hosts.length > 0) $scope.activeIdx(0, v.hosts);
          });
        }
      }
    );
  }

  // 按钮后，转到HostMetrics展示
  $scope.showHost=function(host_metric){
    $scope.show.host=host_metric.host;
    $rootScope.setActiveMonMenuTabByName('mtServiceHostMetrics');
  }

  // 按钮后，转到HostsMetric展示
  $scope.showMetric=function(host_metric){
    $scope.show.metric=host_metric.metric;
    $rootScope.setActiveMonMenuTabByName('mtServiceHostsMetric');
  }

  $scope.init();

}]);
