// 服务 Service
uhpApp.controller('MoniServiceCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
  MonitorBaseController($scope, $rootScope, $timeout);
  $scope.groups = ['hadoop-dfs-namenode','hadoop-dfs-datanode','hadoop-dfs-datanode',
    'hadoop-mapred', 'hadoop-yarn-nodemanager',
    'hbase-master', 'hbase-regionserver'];

  // services
  $scope.init=function(){
    console.debug("----------------------");
    $scope.showInfo();
    /**
     * show.services_metrics = [
     *   { name:,metrics:[{name:,display:,value:}] }  
     * ]
     * show.service = ''
     */
    $rootScope.myHttp('GET', '/monitorback/services_metrics', 
      {}, 
      function(res){
        //[ {name:hdfs, show:[{}]}, {name:yarn, show:[{}]} ]
        $scope.show.services_metrics=res['data'];
        console.debug($scope.show.services_metrics);
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
