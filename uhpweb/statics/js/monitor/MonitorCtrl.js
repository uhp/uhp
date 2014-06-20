function MonitorBaseController($scope, $rootScope, $timeout, $location, anchorSmoothScroll) {
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
  $scope.gotoa = function(id){
    //$location.hash(id);
    //$anchorScroll();
    anchorSmoothScroll.scrollTo(id);
  }
 
  // 激活数组中指定 
  $scope.activeItem = function(item, arr){
    $.each(arr, function(k, v){
      if(v.active == 'active'){
        v.active = '';
      }
      return true;
    });
    item.active = 'active';
  };
  $scope.activeIdx = function(idx, arr){
    $scope.activeItem(arr[idx], arr);
  };
  

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
                magicType : type == 'pid' ? {show: false} : {show: false, type: ['line', 'bar', 'stack']},
                restore : {show: false},
                saveAsImage : {show: true},
                dataZoom: type == 'pie' ? {show: false} : {show: false}
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

    if(bool(metric.unit)){
        if(metric.xtype == 'horizontal'){
            chartOpt.xAxis[0].axisLabel = { formatter:'{value}'+metric.unit }
        } else {
            chartOpt.yAxis[0].axisLabel = { formatter:'{value}'+metric.unit }
        }
    }

    return chartOpt;
  }
  
  // host_metric
  // @target : jquery object[s]
  function draw(target, host_metric){
    target=target.get();
    if(!bool(target)) return;
    var myChart = echarts.init(target,{grid:{x:50,y:30,x2:20,y2:55}});
    var chartOpt = $scope.make_chartOpt(host_metric)
    myChart.setOption(chartOpt);
  }
  
  $scope.draw=function(id, host_metric){
    if(!bool(host_metric)) {
      return false;
    }
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

