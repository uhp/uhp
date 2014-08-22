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
    //var myChart = echarts.init(target,{grid:{x:50,y:30,x2:20,y2:55}});
    var myChart = echarts.init(target,theme);
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
      //console.log(t);
      if(!bool(t)) return;
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
    //return;
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

  var theme_shine = {
      // 默认色板
      color: [
          '#c12e34','#e6b600','#0098d9','#2b821d',
          '#005eaa','#339ca8','#cda819','#32a487'
      ],
  
      // 图表标题
      title: {
          itemGap: 8,
          textStyle: {
              fontWeight: 'normal'
          }
      },
      
      // 图例
      legend: {
          itemGap: 8
      },
      
      // 值域
      dataRange: {
          itemWidth: 15,             // 值域图形宽度，线性渐变水平布局宽度为该值 * 10
          color:['#1790cf','#a2d4e6']
      },
  
      // 工具箱
      toolbox: {
          color : ['#06467c','#00613c','#872d2f','#c47630'],
          itemGap: 8
      },
  
      // 提示框
      tooltip: {
          backgroundColor: 'rgba(0,0,0,0.6)'
      },
  
      // 区域缩放控制器
      dataZoom: {
          dataBackgroundColor: '#dedede',            // 数据背景颜色
          fillerColor: 'rgba(154,217,247,0.2)',   // 填充颜色
          handleColor: '#005eaa'     // 手柄颜色
      },
      
      grid: {
          borderWidth: 0
      },
      
      // 类目轴
      categoryAxis: {
          axisLine: {            // 坐标轴线
              show: false
          },
          axisTick: {            // 坐标轴小标记
              show: false
          }
      },
  
      // 数值型坐标轴默认参数
      valueAxis: {
          axisLine: {            // 坐标轴线
              show: false
          },
          axisTick: {            // 坐标轴小标记
              show: false
          },
          splitArea: {           // 分隔区域
              show: true,       // 默认不显示，属性show控制显示与否
              areaStyle: {       // 属性areaStyle（详见areaStyle）控制区域样式
                  color: ['rgba(250,250,250,0.2)','rgba(200,200,200,0.2)']
              }
          }
      },
      
      timeline : {
          lineStyle : {
              color : '#005eaa'
          },
          controlStyle : {
              normal : { color : '#005eaa'},
              emphasis : { color : '#005eaa'}
          }
      },
  
      // K线图默认参数
      k: {
          itemStyle: {
              normal: {
                  color: '#c12e34',          // 阳线填充颜色
                  color0: '#2b821d',      // 阴线填充颜色
                  lineStyle: {
                      width: 1,
                      color: '#c12e34',   // 阳线边框颜色
                      color0: '#2b821d'   // 阴线边框颜色
                  }
              }
          }
      },
      
      map: {
          itemStyle: {
              normal: {
                  areaStyle: {
                      color: '#ddd'
                  },
                  label: {
                      textStyle: {
                          color: '#c12e34'
                      }
                  }
              },
              emphasis: {                 // 也是选中样式
                  areaStyle: {
                      color: '#e6b600'
                  },
                  label: {
                      textStyle: {
                          color: '#c12e34'
                      }
                  }
              }
          }
      },
      
      force : {
          itemStyle: {
              normal: {
                  linkStyle : {
                      strokeColor : '#005eaa'
                  }
              }
          }
      },
      
      chord : {
          padding : 4,
          itemStyle : {
              normal : {
                  lineStyle : {
                      width : 1,
                      color : 'rgba(128, 128, 128, 0.5)'
                  },
                  chordStyle : {
                      lineStyle : {
                          width : 1,
                          color : 'rgba(128, 128, 128, 0.5)'
                      }
                  }
              },
              emphasis : {
                  lineStyle : {
                      width : 1,
                      color : 'rgba(128, 128, 128, 0.5)'
                  },
                  chordStyle : {
                      lineStyle : {
                          width : 1,
                          color : 'rgba(128, 128, 128, 0.5)'
                      }
                  }
              }
          }
      },
      
      gauge : {
          startAngle: 225,
          endAngle : -45,
          axisLine: {            // 坐标轴线
              show: true,        // 默认显示，属性show控制显示与否
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: [[0.2, '#2b821d'],[0.8, '#005eaa'],[1, '#c12e34']], 
                  width: 5
              }
          },
          axisTick: {            // 坐标轴小标记
              splitNumber: 10,   // 每份split细分多少段
              length :8,        // 属性length控制线长
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: 'auto'
              }
          },
          axisLabel: {           // 坐标轴文本标签，详见axis.axisLabel
              textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                  color: 'auto'
              }
          },
          splitLine: {           // 分隔线
              length : 12,         // 属性length控制线长
              lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                  color: 'auto'
              }
          },
          pointer : {
              length : '90%',
              width : 3,
              color : 'auto'
          },
          title : {
              textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                  color: '#333'
              }
          },
          detail : {
              textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                  color: 'auto'
              }
          }
      },
      
      textStyle: {
          fontFamily: '微软雅黑, Arial, Verdana, sans-serif'
      }
  }
  var theme_macarons = {
      // 默认色板
      color: [
          '#2ec7c9','#b6a2de','#5ab1ef','#ffb980','#d87a80',
          '#8d98b3','#e5cf0d','#97b552','#95706d','#dc69aa',
          '#07a2a4','#9a7fd1','#588dd5','#f5994e','#c05050',
          '#59678c','#c9ab00','#7eb00a','#6f5553','#c14089'
      ],
  
      // 图表标题
      title: {
          itemGap: 8,
          textStyle: {
              fontWeight: 'normal',
              color: '#008acd'          // 主标题文字颜色
          }
      },
      
      // 图例
      legend: {
          itemGap: 8
      },
      
      // 值域
      dataRange: {
          itemWidth: 15,
          //color:['#1e90ff','#afeeee']
          color: ['#2ec7c9','#b6a2de']
      },
  
      toolbox: {
          color : ['#1e90ff', '#1e90ff', '#1e90ff', '#1e90ff'],
          effectiveColor : '#ff4500',
          itemGap: 8
      },
  
      // 提示框
      tooltip: {
          backgroundColor: 'rgba(50,50,50,0.5)',     // 提示背景颜色，默认为透明度为0.7的黑色
          axisPointer : {            // 坐标轴指示器，坐标轴触发有效
              type : 'line',         // 默认为直线，可选为：'line' | 'shadow'
              lineStyle : {          // 直线指示器样式设置
                  color: '#008acd'
              },
              crossStyle: {
                  color: '#008acd'
              },
              shadowStyle : {                     // 阴影指示器样式设置
                  color: 'rgba(200,200,200,0.2)'
              }
          }
      },
  
      // 区域缩放控制器
      dataZoom: {
          dataBackgroundColor: '#efefff',            // 数据背景颜色
          fillerColor: 'rgba(182,162,222,0.2)',   // 填充颜色
          handleColor: '#008acd',    // 手柄颜色
      },
  
      // 网格
      grid: {
          borderColor: '#eee'
      },
  
      // 类目轴
      categoryAxis: {
          axisLine: {            // 坐标轴线
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: '#008acd'
              }
          },
          splitLine: {           // 分隔线
              lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                  color: ['#eee']
              }
          }
      },
  
      // 数值型坐标轴默认参数
      valueAxis: {
          axisLine: {            // 坐标轴线
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: '#008acd'
              }
          },
          splitArea : {
              show : true,
              areaStyle : {
                  color: ['rgba(250,250,250,0.1)','rgba(200,200,200,0.1)']
              }
          },
          splitLine: {           // 分隔线
              lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                  color: ['#eee']
              }
          }
      },
  
      polar : {
          axisLine: {            // 坐标轴线
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: '#ddd'
              }
          },
          splitArea : {
              show : true,
              areaStyle : {
                  color: ['rgba(250,250,250,0.2)','rgba(200,200,200,0.2)']
              }
          },
          splitLine : {
              lineStyle : {
                  color : '#ddd'
              }
          }
      },
  
      timeline : {
          lineStyle : {
              color : '#008acd'
          },
          controlStyle : {
              normal : { color : '#008acd'},
              emphasis : { color : '#008acd'}
          },
          symbol : 'emptyCircle',
          symbolSize : 3
      },
  
      // 柱形图默认参数
      bar: {
          itemStyle: {
              normal: {
                  borderRadius: 5
              },
              emphasis: {
                  borderRadius: 5
              }
          }
      },
  
      // 折线图默认参数
      line: {
          smooth : true,
          symbol: 'emptyCircle',  // 拐点图形类型
          symbolSize: 3           // 拐点图形大小
      },
      
      // K线图默认参数
      k: {
          itemStyle: {
              normal: {
                  color: '#d87a80',       // 阳线填充颜色
                  color0: '#2ec7c9',      // 阴线填充颜色
                  lineStyle: {
                      width: 1,
                      color: '#d87a80',   // 阳线边框颜色
                      color0: '#2ec7c9'   // 阴线边框颜色
                  }
              }
          }
      },
      
      // 散点图默认参数
      scatter: {
          symbol: 'circle',    // 图形类型
          symbolSize: 4        // 图形大小，半宽（半径）参数，当图形为方向或菱形则总宽度为symbolSize * 2
      },
  
      // 雷达图默认参数
      radar : {
          symbol: 'emptyCircle',    // 图形类型
          symbolSize:3
          //symbol: null,         // 拐点图形类型
          //symbolRotate : null,  // 图形旋转控制
      },
  
      map: {
          itemStyle: {
              normal: {
                  areaStyle: {
                      color: '#ddd'
                  },
                  label: {
                      textStyle: {
                          color: '#d87a80'
                      }
                  }
              },
              emphasis: {                 // 也是选中样式
                  areaStyle: {
                      color: '#fe994e'
                  },
                  label: {
                      textStyle: {
                          color: 'rgb(100,0,0)'
                      }
                  }
              }
          }
      },
      
      force : {
          itemStyle: {
              normal: {
                  linkStyle : {
                      strokeColor : '#1e90ff'
                  }
              }
          }
      },
  
      chord : {
          padding : 4,
          itemStyle : {
              normal : {
                  lineStyle : {
                      width : 1,
                      color : 'rgba(128, 128, 128, 0.5)'
                  },
                  chordStyle : {
                      lineStyle : {
                          width : 1,
                          color : 'rgba(128, 128, 128, 0.5)'
                      }
                  }
              },
              emphasis : {
                  lineStyle : {
                      width : 1,
                      color : 'rgba(128, 128, 128, 0.5)'
                  },
                  chordStyle : {
                      lineStyle : {
                          width : 1,
                          color : 'rgba(128, 128, 128, 0.5)'
                      }
                  }
              }
          }
      },
  
      gauge : {
          startAngle: 225,
          endAngle : -45,
          axisLine: {            // 坐标轴线
              show: true,        // 默认显示，属性show控制显示与否
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: [[0.2, '#2ec7c9'],[0.8, '#5ab1ef'],[1, '#d87a80']], 
                  width: 10
              }
          },
          axisTick: {            // 坐标轴小标记
              splitNumber: 10,   // 每份split细分多少段
              length :15,        // 属性length控制线长
              lineStyle: {       // 属性lineStyle控制线条样式
                  color: 'auto'
              }
          },
          axisLabel: {           // 坐标轴文本标签，详见axis.axisLabel
              textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                  color: 'auto'
              }
          },
          splitLine: {           // 分隔线
              length :22,         // 属性length控制线长
              lineStyle: {       // 属性lineStyle（详见lineStyle）控制线条样式
                  color: 'auto'
              }
          },
          pointer : {
              width : 5,
              color : 'auto'
          },
          title : {
              textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                  color: '#333'
              }
          },
          detail : {
              textStyle: {       // 其余属性默认使用全局文本样式，详见TEXTSTYLE
                  color: 'auto'
              }
          }
      },
      
      textStyle: {
          fontFamily: '微软雅黑, Arial, Verdana, sans-serif'
      }
  }

  var theme = theme_shine;
  theme.grid = {x:50,y:30,x2:20,y2:55};
}

// @dep
uhpApp.controller('MonitorCtrl', ['$scope', '$rootScope', '$http', '$sce','$timeout', function($scope, $rootScope, $http, $sce, $timeout){
}]);

