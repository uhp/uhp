function MonitorBaseController($scope, $rootScope, $timeout) {
  // 数据结构
  // 注意绘图使用的数据结构
  // host_metric:{host:,metric:{name:,display:,unit:,chartType:},x:,y:}
  // group_metric:{metric:,x:,y:}

  // 公共变量
  // 公共函数
  $rootScope.formatIdName=function(name){
    return 'draw_' + parseInt(Math.random() * 1000000000);
  };

  $rootScope.showHostsMetric = function(newValue, oldValue, scope){
    if(!bool(scope.show.precision) || !bool(scope.show.metric)) return;
    //http://hadoop1:59990/monitorback/show_hosts_metric?hosts=hadoop1&hosts=hadoop4&hosts=hadoop5&metric=disk_free&precision=p7200
    $rootScope.myHttp('POST', '/monitorback/show_hosts_metric', 
      {precision:$scope.show.precision, metric:$scope.show.metric, hosts:$scope.show.hosts}, 
      function(res){
        $scope.show.hosts_metric=[];
        angular.forEach(res['data'], function(v, k){
          v.metric = scope.show.metric;
          xfunc = $scope.default_xfunc;
          v.x = $.map(v.x, xfunc);
          this.push(v);
        }, $scope.show.hosts_metric);
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
          xfunc = $scope.default_xfunc;
          v.x = $.map(v.x, xfunc);
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

  // metric:{metric:, x:[], y:[]}
  // metric:{metric:, x:[], y:{host:[]}}
  // metric:[{metric:,x:[], xtype:'horizontal', series:[{name:,type:,data:[]}]}]
  // metric:[{metric:,series:[{name:,type:,data:[]}]}] # pie 分布图
  $scope.make_chartOpt=function(metric){
    console.debug(metric);
 
    type = "axis";

    //转换null值为echart要求格式
    if(metric.series){//新的数据格式，可以绘制多个指标在同一个图
      $.each(metric.series, function(k, v){
        if(v.type == "pie"){ // 分布图已经计算好
          type = "pie";
        } else {
          metric.series[k].data = $.map(v.data, function(n){
            return (n===null)?'-':n;
          });
        }
      });
    } else { //旧的数据格式
      if($.isArray(metric.y)){ //单个指标
        metric.y = $.map(metric.y, function(n){
          return (n===null)?'-':n;
        });
      } else { //多个指标
        $.each(metric.y, function(k, vs){
          metric.y[k] = $.map(vs, function(n){
            return (n===null)?'-':n;
          });
        });
      }
    }

    function legendData(){
      if(metric.series){
        var retu = [];
        var temp = type == 'pie' ? metric.series[0].data : metric.series;
        $.each(temp, function(k, v){
          retu.push(v.name);
        }); 
        return retu;
      }
      if($.isArray(metric.y)) return [metric.metric];
      var retu = [];
      $.each(metric.y, function(k, v){
        retu.push(k);
      }); 
      return retu;
    }

    function series(){
      if(metric.series){
        //$.each(metric.series, function(k, v){
        //  v.barWidth=10; 
        //});
        return metric.series;
      }
      if($.isArray(metric.y)) return [ { name: metric.metric, type:metric.chartType||'line', data:metric.y } ];
      var retu = [];
      $.each(metric.y, function(k, v){
        s = {name:k, type:'line', data:v}
        retu.push(s);
      }); 
      return retu;
    }

    chartOpt = {
        tooltip : type == 'pie' ? { trigger: 'item' } : { trigger: 'item' },
        legend  : type == 'pie' ? { orient:'vertical', x:'left', data:legendData() } : { x:'left', data:legendData() },
        toolbox: {
            show : true,
            feature : {
                mark : {show: false},
                dataView : {show: true, readOnly: true},
                magicType : type == 'pid' ? {show: false} : {show: true, type: ['line', 'bar', 'stack']},
                restore : {show: false},
                saveAsImage : {show: true},
                dataZoom: type == 'pie' ? {show: false} : {show: true}
            }
        },
        dataZoom: type == 'pie' ? {show: false} : {show: true},
        calculable : false,
        series : series()
    }

    if(type != 'pie'){
        xAxis = function() {return [ { type : 'category', boundaryGap : true, data : metric.x } ];}
        yAxis = function() {return [ { type : 'value', splitArea : {show:false} } ];};
        if(metric.xtype == 'horizontal') {
          tmp = xAxis;
          xAxis = yAxis;
          yAxis = tmp;
        }
        chartOpt.xAxis=xAxis();
        chartOpt.yAxis=yAxis();
    }

    if(bool(metric.metric) && bool(metric.metric.unit)){
      chartOpt.yAxis[0].axisLabel = { formatter:'{value}'+metric.metric.unit }
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
    var chartOpt = $scope.make_chartOpt(host_metric)
    console.debug(chartOpt);
    myChart.setOption(chartOpt);
  }
  
  $scope.draw=function(id, host_metric){
    if(!bool(host_metric)) {
      console.debug('$scope.draw null metric');
      console.debug(host_metric);
      return false;
    }
    console.debug("draw ...")
    // 等待界面target元素绘制完成
    $timeout(function(){ 
      var t = $(id);
      // 响应宽度变化
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
      calculable : false,
      series : [        
          {
              name:rose_group_metric.name,
              type:'pie',
              radius : '55%',
              data:rose_group_metric.data
          }
      ]
    }; 
    var myChart = echarts.init(target,{grid:{x:40,y:30,x2:10,y2:55}});
    myChart.setOption(chartOpt);
  }

  $scope.drawRose=function(id, rose_group_metric){
    if(!bool(rose_group_metric)) {
      return false;
    }
    console.debug("draw ...")
    // 等待界面target元素绘制完成
    $timeout(function(){ 
      var t = $(id);
      $scope.$watch(function(){return t.width();}, function(newValue, oldValue){
        if(newValue <= 0) return;
        var w = t.width();
        var h = t.height();
        if(h < 10){
          h = w * 0.9;
          t.height(h);
        }
        console.debug('id:'+id);
        drawRose(t, rose_group_metric); 
      });
    }, 300);
  }; 
  
  $scope.showBigDistribution=function(dist_metric){
		$("#bigDrawModal").modal();
    drawRose($("#draw_big"), dist_metric);
  }
  
  $scope.drawDistribution = function(targetSelect, dist_metric){
    $scope.drawRose(targetSelect, dist_metric);
  }
}

// @dep
uhpApp.controller('MonitorCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
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

  $scope.fetchHostCurrentOverview = function(){
    //$rootScope.myHttp('GET', '/statics/static_data/monitor/fetch_host_current_overview', 
    $rootScope.myHttp('GET', '/monitorback/fetch_host_current_overview', 
      {}, 
      function(res){
        // data:[{name,x:[],series:[{name:,type:,data:[]}]}]
        $scope.show.all_host_overview = res['data'];
        //angular.forEach($scope.show.all_host_overview, function(v, k){
        //  v.chartType = 'bar';
        //  console.debug(v);
        //});
      }
    );
  }

  $scope.init = function(){
    $scope.showInfo();
    console.debug($scope.show);
    $scope.fetchHostCurrentOverview();
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
      $scope.column = response['column']
			$scope.data = response['data'];
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

  $scope.add_table_record=function(){
    $scope.new_record = {};
    $scope.recordAction="insert";
		$("#monitorConfModal").modal();
  }
  
  $scope.ready_edit_record=function(record){
    console.log(record);
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
    console.log(sql);
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
    console.log($scope.new_record);
    $scope.dealRecord($scope.new_record)
  }

  $scope.delete_record=function(idx, record){
    var update_record = {id:record[0]};
    //for(i in $scope.column){
    //  update_record[$scope.column[i]] = record[i];
    //}
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

}]);
