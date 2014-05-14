function MonitorBaseController($scope, $rootScope, $timeout) {
  // 数据结构
  // 注意绘图使用的数据结构
  // host_metric:{host:,metric:{name:,display:,unit:,chartType:},x:,y:}
  // group_metric:{metric:,x:,y:}

  // 公共变量
  // 公共函数
  $rootScope.formatIdName=function(name){
    return name.replace(/\./g,"_");
  };

  $rootScope.showHostsMetric = function(newValue, oldValue, scope){
    console.log('precision:' + scope.show.precision);
    console.log('metric:' + scope.show.metric);
    if(!bool(scope.show.precision) || !bool(scope.show.metric)) return;
    $rootScope.myHttp('POST', '/monitorback/show_hosts_metric', 
      {precision:scope.show.precision, metric:scope.show.metric, hosts:scope.show.hosts}, 
      function(res){
        scope.show.hosts_metric=[];
        angular.forEach(res['data'], function(v, k){
          v.metric = scope.show.metric;
          this.push(v);
        }, scope.show.hosts_metric);
      }
    );
  }

  $rootScope.showHostMetrics = function(newValue, oldValue, scope){
    console.log('precision:' + scope.show.precision);
    console.log('host:' + scope.show.host);
    if(!scope.show.precision || !scope.show.host) return;
    $rootScope.myHttp('GET', '/monitorback/show_host_metrics', 
      {precision:scope.show.precision, host:scope.show.host, groups:scope.groups}, 
      function(res){
        scope.show.host_metrics=[];
        angular.forEach(res['data'], function(v, k){
          v.host = scope.show.host;
          this.push(v);
        }, scope.show.host_metrics);
      }
    );
  }

  // scope变量
  $scope.groups = []; //指标组
  $scope.show={};

  // scope函数
  $scope.showInfo = function(){
    /**
     * for show  
     * { precisions:[{name:,display:}], precision:'',
     *   metrics:[{name:,display:}], metric:'',
     *   hosts:[''], host:'',
     *   hosts_metric:[{host:, x:, y:}],
     *   host_metrics:[{metric:, x:, y:}]
     * }
     * host_metric = {host:,metric:,x:,y:}
     * host_metric_chartOpt = make_chartOpt(host_metric)
     **/
    $rootScope.myHttp('GET', '/monitorback/show_info', 
      {groups:$scope.groups}, 
      function(res){
        $.extend($scope.show, res['data']);
      }
    );
    $scope.$watch(function(){return $scope.show.precision + $scope.show.metric;}, $rootScope.showHostsMetric);
    $scope.$watch(function(){return $scope.show.precision + $scope.show.host;}, $rootScope.showHostMetrics);
    $scope.$watch(function(){return $scope.show.precision;},function(){
      if(!$scope.show.precision) return;
      $scope.show.precisionSec=parseInt($scope.show.precision.substr(1));
    });

  }

  // scope函数
 
  $scope.default_xfunc=function(n){
    //时间转换，从时间戳转为可读
    sec = $scope.show.precisionSec; 
    return sec>86400 ? date('n-j/H:i', n): date('H:i', n);
  }

  $scope.NO_XFUNC=function(n){
    return n;
  }

  // host_metric:{metric:,x:,y:}
  $scope.make_chartOpt=function(host_metric){
    //x轴转换  
    console.debug(host_metric);
    xfunc = host_metric.xfunc || $scope.default_xfunc;
    if(xfunc != $scope.NO_XFUNC){
      host_metric.x = $.map(host_metric.x, xfunc);
    }
    
    //转换null值为echart要求格式
    host_metric.y = $.map(host_metric.y, function(n){
      return (n===null)?'-':n;
    });

    chartOpt = {
        tooltip : { trigger: 'axis' },
        legend: { x:'left', data:[host_metric.metric] },
        toolbox: {
            show : true,
            feature : {
                mark : {show: false},
                dataView : {show: false, readOnly: false},
                magicType : {show: true, type: ['line', 'bar', 'stack']},
                restore : {show: false},
                saveAsImage : {show: true},
                dataZoom:{show: true}
            }
        },
        dataZoom: {show:true},
        calculable : false,
        xAxis : [ { type : 'category', boundaryGap : true, data : host_metric.x } ],
        yAxis : [ { type : 'value', splitArea : {show:true} } ],
        series : [ { name:$scope.show.metric, type:host_metric.chartType||'line', data:host_metric.y } ]
    }
    if(bool(host_metric.metric.unit)){
      chartOpt.yAxis[0].axisLabel = { formatter:'{value}'+host_metric.metric.unit }
    }
    return chartOpt;
  }
  
  // host_metric
  // @target : jquery object[s]
  function draw(target, host_metric){
    target=target.get();
    console.debug(target);
    if(!bool(target)) return;
    var myChart = echarts.init(target,{grid:{x:40,y:30,x2:10,y2:55}});
    myChart.setOption($scope.make_chartOpt(host_metric)); // ~ setOption
  }
  
  $scope.draw=function(id, host_metric){
    console.debug("draw ...")
    // 等待界面target元素绘制完成
    $timeout(function(){ 
      var t = $(id);
      $scope.$watch(function(){return t.width();}, function(newValue, oldValue){
        if(newValue <= 0) return;
        var w = newValue;
        var h = t.height();
        if(h < 10){
          h = w * 0.4;
          t.height(h);
        }
        console.debug('id:'+id);
        console.debug(t);
        console.debug(t.width());
        console.debug(t.height());
        draw(t, host_metric); 
      });
    }, 300);
  }
  
  $scope.showBig=function(host_metric){
		$("#bigDrawModal").modal();
    draw($("#draw_big"), host_metric);
  }
 
  // 绘制玫瑰图 
  // @rose_group_metric:{name:,data:[{value:,name:}]}
  function drawRose(target, rose_group_metric){
    target=target.get();
    console.debug(target);
    if(!bool(target)) return;
    chartOpt = { 
      tooltip : { trigger: 'item', formatter: "{a} <br/>{b} : {c} ({d}%)" },
      toolbox: {
          show : true,
          feature : {
              mark : {show: false},
              dataView : {show: true, readOnly: true},
              restore : {show: false},
              saveAsImage : {show: true}
          }
      },
      calculable : true,
      series : [        
          {
              name:rose_group_metric.name,
              type:'pie',
              radius : ['20%', '75%'],
              roseType : 'area',
              data:rose_group_metric.data
          }
      ]
    }; 
    var myChart = echarts.init(target,{grid:{x:40,y:30,x2:10,y2:55}});
    myChart.setOption(chartOpt);
  }

  $scope.drawRose=function(id, rose_group_metric, limit){
    if(angular.isUndefined(limit)) {
      limit = 20;
    }
    if(limit < 0) return false;
    // 等待界面target元素绘制完成
    $timeout(function(){ 
      var t = $(id);
      var w = t.width();
      if(w == 0) return $scope.drawRose(id, rose_group_metric, limit-1);
      var h = t.height();
      if(h < 10){
        h = w;
        t.height(h);
      }
      console.debug('id:'+id);
      drawRose(t, rose_group_metric); 
    }, 500);
  }; 
}

// @dep
uhpApp.controller('MonitorCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
}]);

// 概览
uhpApp.controller('MoniOverviewCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
  MonitorBaseController($scope, $rootScope, $timeout);
 
  var labelColor = ['label-danger','label-warning','label-success'];

  $scope.mapColor = function(v){
    return labelColor[parseInt(v/34)]; 
  }

  $scope.fetch_current_healths = function(){
    // healths: [ {name:,display:,x:[],y:[]} ]
    $scope.show.healths = [
      {
        type:'single',
        name:'host',
        display:'机器健康度',
        value:90,
        x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
        y:[100,81,98,17,0]
      },
      {
        type:'multi',
        name:'service',
        display:'服务健康度',
        group:[
          {
            name:'zookeeper',
            display:'Zookeeper',
            value:80,
            x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
            y:[100,81,98,17,0]
          },
          {
            name:'hdfs',
            display:'hdfs',
            value:80,
            x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
            y:[100,81,98,17,0]
          },
          {
            name:'yarn',
            display:'yarn',
            value:80,
            x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
            y:[100,81,98,17,0]
          }
        ]
      },
      {
        type:'multi',
        name:'job',
        display:'作业状况',
        group: [
          {
            name:'',
            display:'运行作业',
            value:"23/30"
          },
          {
            name:'',
            display:'资源占用',
            value:"40/40G"
          }
        ]
      }
    ];
    
    var host_health_history = {
      type:'single',
      metric:'机器健康度历史',
      x:[1399973996, 1399973936, 1399973876, 1399973816,1399973756,1399973696,1399973636,1399973576,1399973516,1399973456],
      y:[100,90,95,100,100,90,80,60,80,100]
    };
    
    var service_health_history = {
      type:'multi',
      metric:'服务健康度历史',
      group:[
        {
          metric:'Zookeeper',
          x:[1399973996, 1399973936, 1399973876, 1399973816,1399973756,1399973696,1399973636,1399973576,1399973516,1399973456],
          y:[100,90,95,100,100,90,80,60,80,100]
        },
        {
          metric:'Hdfs',
          x:[1399973996, 1399973936, 1399973876, 1399973816,1399973756,1399973696,1399973636,1399973576,1399973516,1399973456],
          y:[100,90,95,100,100,90,80,60,80,100]
        },
        {
          metric:'Yarn',
          x:[1399973996, 1399973936, 1399973876, 1399973816,1399973756,1399973696,1399973636,1399973576,1399973516,1399973456],
          y:[100,90,95,100,100,90,80,60,80,100]
        }
      ]
    };
    
    $scope.show.all_health_history = [host_health_history,service_health_history];

  }

  $scope.init = function(){
    $scope.showInfo();
    $scope.fetch_current_healths();
  }

  $scope.init();

}]);

uhpApp.controller('MoniHostCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
  MonitorBaseController($scope, $rootScope, $timeout);
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
 
  $scope.init = function(){
    $scope.showInfo();
    console.debug($scope.show);
    // group_metric = {metric:{},x:,y:}

    var all_load = {
      metric:'负载',
      chartType:'bar',
      x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
      y:[2.5,3.0,2.2,3.4,4]
    };
    
    var all_net = {
      metric:'网络',
      chartType:'bar',
      x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
      y:[3.3,5.3,3.2,4.4,5]
    };

    var all_disk = {
      metric:'存储',
      chartType:'bar',
      x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
      y:[3.3,5.3,3.2,4.4,5]
    };

    var all_mem = {
      metric:'内存',
      chartType:'bar',
      x:['hadoop1','hadoop2','hadoop3','hadoop4','hadoop5'],
      y:[20,30,22,34,40]
    };

    $scope.show.all_host_overview = [all_load, all_net, all_mem, all_disk];

    //$scope.draw_1();
    //$scope.drawAllHostLoadDistribution();
  }
  
  $scope.drawAllHost=function(targetSelect, group_metric){
    //var host_metric=$scope.show.all_host_load;
    console.debug(targetSelect);
    console.debug(group_metric);
    var host_metric=group_metric;
    if(!bool(host_metric.xfunc)){
      host_metric.xfunc=$scope.NO_XFUNC;
    }
    $scope.draw(targetSelect,host_metric);
  }
 
  $scope.drawAllHostDistribution = function(targetSelect, group_metric){
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
    $scope.drawRose(targetSelect,rose_group_metric);
  }
  
  //$scope.draw_2=function(){$scope.draw('#all_disk_use', $scope.show.all_disk_use);}
  //$scope.draw_3=function(){$scope.draw('#all_resource_use', $scope.show.all_resource_use);}
  //$scope.draw_4=function(){$scope.draw('#all_net_use', $scope.show.all_net_use);}

  $scope.init();

}]);

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

uhpApp.controller('MoniJobCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){

}]);

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
      console.log("query ok!");
      is_refresh = !!is_refresh;
      if(!is_refresh){
        $scope.column = response['column']
      }
      if(is_refresh){
        $scope.copy_array(response['data'], $scope.data);
      }else{
			  $scope.data = response['data'];
      }
      console.log($scope.data);
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
  
  function query_alarm_assist() {
    $scope.sql_table = "alarm_assist";
    $scope.sql = "select * from "+$scope.sql_table;
    $scope.query();
  }

  $scope.add_table_record=function($event){
    $scope.is_adding_new_record = true;
  }
  $scope.giveup_record=function($event){
    $scope.is_adding_new_record = false;
    $scope.new_record = {};
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
    console.log(sql);
    return sql;
  }

  $scope.save_new_record=function($event){
    console.log($scope.new_record);
		if(!$scope.new_record) return;
    var sql = make_sql("insert", $scope.sql_table, $scope.new_record);
		$http({
	    method: 'POST',
	    url: '/adminback/manual_execute',
	    params:  { sql : sql }
	  }).success(function(response, status, headers, config){
	  	if(response["ret"]!="ok"){
	      	$rootScope.alert("提交失败 ("+response["msg"]+")");
          return;
	    }
      $scope.giveup_record();
      // 刷表格
      $scope.query(true);
	  }).error(function(data, status) {
	  	$rootScope.alert("发送manual_insert请求失败");
	  });
  }

  $scope.ready_edit_record=function(record){
    console.log(record);
    $scope.edit_record=$scope.copy_array(record);
    console.log($scope.edit_record);
  }

  $scope.giveup_edit_record=function(record){
    $scope.copy_array($scope.edit_record,record);
    $scope.edit_record=[];
  }

  $scope.copy_array=function(a,b){
    if(!b){ 
      var b = [];
    }else{
      b.splice(0, b.length)
    }
    for(i=0;i<a.length;i++){
      b.push(a[i]);
    }
    return b;
  }

  $scope.update_record=function(idx,record){
    console.log($scope.column);
    console.log(record);
    console.log($scope.edit_record);
    var update_record = {};
    for(i in $scope.column){
      update_record[$scope.column[i]] = record[i];
    }
    console.log(update_record);
    var sql = make_sql("update", $scope.sql_table, update_record);
		$http({
	    method: 'POST',
	    url: '/adminback/manual_execute',
	    params:  { sql : sql }
	  }).success(function(response, status, headers, config){
	  	if(response["ret"]!="ok"){
	      	$rootScope.alert("提交失败 ("+response["msg"]+")");
          return;
	    }
      $scope.edit_record = [];
      $scope.is_editing[idx] = false;
	  }).error(function(data, status) {
	  	$rootScope.alert("发送manual update请求失败");
	  });
  }

  $scope.delete_record=function(idx, record){
    var update_record = {};
    for(i in $scope.column){
      update_record[$scope.column[i]] = record[i];
    }
    console.log(update_record);
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
  $scope.edit_record = [];
  $scope.is_editing = [];

}]);
