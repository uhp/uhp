
uhpApp.controller('MoniJobCtrl', ['$scope', '$rootScope', '$http', '$sce', '$timeout', '$interval', function($scope, $rootScope, $http, $sce, $timeout, $interval){
    MonitorBaseController($scope, $rootScope, $timeout);
 
    $scope.loadRunningState=function(){
        $http({
            method: 'GET',
            url: '/monitorback/app_running_state'
        }).success(function(response, status, headers, config){
            $scope.app_state=response['clusterMetrics']
        }).error(function(data, status) {
            $rootScope.alert("发送app_running_state请求失败");
        });
    }

    $scope.loadRunningApp=function(){
        $http({
            method: 'GET',
            //url: '/static/static_data/monitor/app_running'
            url: '/monitorback/app_running'
        }).success(function(response, status, headers, config){
            $scope.rmport=response['rmport']
            $scope.rmhost=response['rmhost']
            $scope.queues=$scope.formatQueues(response['queues'])
            $scope.queueMeta={}
            for(var queueName in $scope.queues){
                var queue = $scope.queues[queueName]
                var temp = {}
                temp['apps']=Object.keys(queue).length
                temp['collect_app']=0
                temp['run_map']=0
                temp['run_reduce']=0
                temp['todo_map']=0
                temp['todo_reduce']=0
                $scope.queueMeta[queueName]=temp
            }
            //run for app proxy for every app
            for(var queue in $scope.queues ){
                for(var appid in $scope.queues[queue]){
                    $scope.update_appid_info(queue,appid)
                }
            }
        }).error(function(data, status) {
            $rootScope.alert("发送app_running请求失败");
        });
    }

    $scope.update_appid_info=function(queue,appid){
        $http({
            method: 'GET',
            url: '/monitorback/app_proxy',
            params:{
                "appid": appid
            }
        }).success(function(response, status, headers, config){
            for(var index in $scope.appkeyList){
                var key = $scope.appkeyList[index]
                $scope.queues[queue][appid][key]=response[key]
            }
            $scope.queues[queue][appid]['amTime']=$scope.formatElapsedTime(response['amTime'])
        }).error(function(data, status) {
            $rootScope.alert("发送app_proxy请求失败");
        });

    }

    $scope.formatQueues=function(queues){
        var re = {}
        for(var name in queues){
            re[name]={}
            for(var appid in queues[name]){
                var temp=$scope.init_app() 
                for(var key in  queues[name][appid]){
                    temp[key]=$scope.format(key,queues[name][appid][key])
                }
                re[name][appid]=temp
            }
        }
        return re;
    }

    $scope.init_app=function(){
        var re={}
        re['amTime']='-';
        for(var index in $scope.appkeyList){
            var key = $scope.appkeyList[index]
            re[key]='-'
        }
        return re
    }

    $scope.format=function(key,value){
        if( key == "startedTime"){
            return unix_to_datetime(value);
        }
        else if( key == "progress"){
            return value.toFixed(1)+"%";
        }
        else if( key == "elapsedTime"){
            return $scope.formatElapsedTime(value)
        }
        else if(key =="amHostHttpAddress"){
            return $scope.getNodeFromAddress(value)
        }
        else if(key =="id"){
            last = value.lastIndexOf("_")
            return value.substring(last+1)
        }
        return value
    }

    $scope.formatAppid=function(appid){
        last = appid.lastIndexOf("_")
        return appid.substring(last+1)
    }

    $scope.getNodeFromAddress=function(address){
        length = address.indexOf(":");
        return address.substring(0,length);
    }

    $scope.formatElapsedTime=function(elapsedTime){
        if( elapsedTime=="x" ) return elapsedTime;
        var sec = Math.floor(elapsedTime/1000);
        var min = Math.floor(sec/60);
        var sec = sec - min*60;
        return min+"m"+sec+"s";
    }

    $scope.loadWaittingApp=function(){
        $http({
            method: 'GET',
            url: '/monitorback/app_waitting'
        }).success(function(response, status, headers, config){
            $scope.waitting_app=response['waitting']['app']
            for(var index in $scope.waitting_app){
                var elapsedTime = $scope.waitting_app[index]['elapsedTime']
                $scope.waitting_app[index]['elapsedTime'] = $scope.formatElapsedTime(elapsedTime)
            }
        }).error(function(data, status) {
            $rootScope.alert("发送app_running请求失败");
        });
       
    }

    $scope.runningQuery=function(){
        $scope.loadRunningState()
        $scope.loadRunningApp()
        $scope.loadWaittingApp()
        $scope.has_query=true
    }

    function convertResult(fields, result){
      // [ [time, value,...] ]
      // [ {metric:,x:[],y:[]} ]
      metrics = [];
      $.each(fields, function(i, n){
          metrics.push({metric:n,x:[],y:[]});
      });

      $.each(result, function(i, n){
          $.each(n, function(j, v){
              if(j == 0){
                  v = parseInt(v);
                  $.each(metrics, function(k, z){
                      z.x.push(v);
                  });
              } else {
                  metrics[j-1].y.push(v);
              }
          });
      });
      return metrics;
    }


    //for rm query
    $scope.rmQuery=function(){
        var fields = $scope.getRmFieldParams();
        $http({
            method: 'GET',
            url: '/monitorback/rm_query',
            params:{
                "fields"          : fields,
                "happenTimeSplit" : $scope.rm_split*60,
                "happenTimeMin"   : get_unix_time() - (parseInt($scope.rm_time)*60),
                "happenTimeMax"   : get_unix_time()
            }
        }).success(function(response, status, headers, config){
            $scope.rm = response
            // 数据格式转换 [[]] => [{}]
            // [ {metric:,x:[],y:[]} ]
            $scope.rm.metrics = convertResult(fields, $scope.rm.result);
            xfunc=function(n){
                return $scope.rm_time>1440 ? date('n-j/H:i', n): date('H:i', n);
            }
            $.each($scope.rm.metrics, function(i, n){
                n.x = $.map(n.x, xfunc);
            });
        }).error(function(data, status) {
            $rootScope.alert("发送app_running请求失败");
        });
    }

    $scope.getRmFieldParams=function(){
        var temp = []
        for(var index in $scope.selected_rm_fields){
            var value = $scope.selected_rm_fields[index]
            if( value == "app" ){
                temp.push("appNum")
                temp.push("finishedApp")
                temp.push("failedApp")
                temp.push("killedApp")
                temp.push("notSuccApp")
            }   
            else if( value == "map" ){
                temp.push("mapNum")
                temp.push("mapTime")
                temp.push("failMap")
            }   
            else if( value == "reduce" ){
                temp.push("reduceNum")
                temp.push("reduceTime")
                temp.push("failReduce")
            }   
            else if( value == "file" ){
                temp.push("fileRead")
                temp.push("fileWrite")
            }    
            else if( value == "hdfs" ){
                temp.push("hdfsRead")
                temp.push("hdfsWrite")
            }    
            else{
                temp.push(value)
            }   
        }   
        return temp;
    }
    
    // @return [ {metric:, x:[], y:{host:[]}} ]
    function convertResultForMultiHost(fields, hosts, result){
      // [ [time,host,field_value,field_value2,...] ]
      // [ {metric:,x:[],[{host:,y:[]}]} ]
      
      // 先进行一次整理，方便后面使用
      times= []; // [time]
      data = {}; // {time:{host:{field:}}}
      $.each(result, function(i, n){
        time = parseInt(n[0]);
        if(!(time in data)){
          times.push(time);
          data[time] = {}
        }
        
        host = n[1];
        data[time][host] = {}

        values = n.slice(2);
        $.each(values, function(j, v){
          field = fields[j];
          data[time][host][field] = v;
        });
      });

      // 构建 metrics
      // [ {metric:, x:[], y:{host:[]}} ]
      metrics = [];
      $.each(fields, function(i, f){
        metric = {metric:f,x:[],y:{}};
        $.each(times, function(j, t){
          metric.x.push(t);
          $.each(hosts, function(k, h){
            if(!(h in metric.y)){
              metric.y[h] = [];
            }
        
            v = null;
            if(h in data[t]){
              v = data[t][h][f];
            }
            metric.y[h].push(v);
          });
        }); 
        metrics.push(metric);
      });

      return metrics;
    }

    //for nm query
    $scope.nmQuery=function(){
        var fields = $scope.getNmFieldParams();
        $http({
            method: 'GET',
            url: '/monitorback/nm_query',
            params:{
                "fields"          : fields,
                "hosts"           : $scope.selected_nm_hosts,
                "happenTimeSplit" : $scope.nm_split*60,
                "happenTimeMin"   : get_unix_time() - (parseInt($scope.nm_time)*60),
                "happenTimeMax"   : get_unix_time()
            }
        }).success(function(response, status, headers, config){
            $scope.nm = response
            // 数据格式转换 [[]] => [{}]
            // 同一指标，多实体对比
            // [ {metric:,x:[],y:[]} ]
            $scope.nm.metrics = convertResultForMultiHost(fields, $scope.selected_nm_hosts, $scope.nm.result);
            xfunc=function(n){
                return $scope.nm_time>1440 ? date('n-j/H:i', n): date('H:i', n);
            }
            $.each($scope.nm.metrics, function(i, n){
                n.x = $.map(n.x, xfunc);
            });
        }).error(function(data, status) {
            $rootScope.alert("发送app_nmquery请求失败");
        });
    }

    $scope.getNmFieldParams=function(){
        var temp = []
        angular.forEach($scope.selected_nm_fields, function(value, k){ 
            if( value  == "map" ){
                temp.push("mapNum")
                temp.push("mapTime")
                temp.push("failMap")
            }   
            else if( value == "reduce" ){
                temp.push("reduceNum")
                temp.push("reduceTime")
                temp.push("failReduce")
            }   
            else if( value == "file" ){
                temp.push("fileRead")
                temp.push("fileWrite")
            }    
            else if( value == "hdfs" ){
                temp.push("hdfsRead")
                temp.push("hdfsWrite")
            }    
            else{
                temp.push(value)
            }   
        });
        return temp;
    }

    //for apps query
    $scope.appQuery=function(){
        $scope.loadAppSum()
        $scope.nowPage = 1
        $scope.loadAppList()
    }

    $scope.loadAppSum=function(){
        $http({
            method: 'GET',
            url: '/monitorback/app_sum',
            params:{
                "where": $scope.getWhere()   
            }
        }).success(function(response, status, headers, config){
            $scope.appsum=response['resultRecord']
            $scope.setMaxPage($scope.appsum['appidCount'])
        }).error(function(data, status) {
            $rootScope.alert("发送app_sum请求失败");
        });
    }

    $scope.loadAppList=function(){
        $http({
            method: 'GET',
            url: '/monitorback/app_list',
            params:{
                "where" : $scope.getWhere(),
                "offset" : ( $scope.nowPage -1) * $scope.limit,
                "limit" : $scope.limit,
                "orderField" : $scope.orderField,
                "orderDirection" : $scope.orderDirection
            }
        }).success(function(response, status, headers, config){
            $scope.applist=$scope.formatApplist(response['applist'])
            $scope.rmhost=response['rmhost']
            $scope.rmport=response['rmport']
        }).error(function(data, status) {
            $rootScope.alert("发送app_list请求失败");
        });
    }

    $scope.rate=function(small,big){
        return (small*100/big).toFixed(1)
    }

    $scope.toGSize=function(value){
        return toGSize(value)
    }

    $scope.formatApplist=function(applist){
        var re=[]
        for(var index in applist){
            var app = applist[index];
            var temp = {}
            temp['id']=$scope.formatAppid(app[0])
            temp['appid']=app[0]
            temp['user']=app[1]
            temp['name']=app[2]
            temp['queue']=app[3]
            temp['start']=unix_to_datetime(app[4]*1000)
            temp['end']=unix_to_datetime(app[5]*1000)
            temp['state']=$scope.stateDict[app[6]]
            temp['finalStatus']=$scope.finalStatusDict[app[7]]
            temp['retry']=app[8]
            temp['map_total']=app[9]
            temp['map_fini']=app[10]
            temp['map_local']=app[11]
            temp['reduce_total']=app[12]
            temp['reduce_fini']=app[13]
            temp['local_read']=toMSize(app[14])
            temp['local_write']=toMSize(app[15])
            temp['hdfs_read']=toMSize(app[16])
            temp['hdfs_write']=toMSize(app[17])
            re.push(temp)
        }
        return re
    }

    $scope.getWhere=function(){
        //获取where
        var likeParams = {}
        var where = " 1 " 
        if($scope.filterId != null ) {
            where = where + ' and appid like "o|o'+$scope.filterId+'o|o" '
        }
        if($scope.filterUser != null ) {
            where = where + ' and user like "o|o'+$scope.filterUser+'o|o" '
        } 
        if($scope.filterName != null ) {
            where = where + ' and name like "o|o'+$scope.filterName+'o|o" '
        } 
        if($scope.filterQueue != null ) {
            where = where + ' and queue like "o|o'+$scope.filterQueue+'o|o" '
        } 
        if($scope.filterState != null ) {
            where = where + ' and state = "'+$scope.filterState+'" '
        }
        if($scope.filterFinalStatus != null ) {
            where = where + ' and finalStatus = "'+$scope.filterFinalStatus+'" '
        }
        
        //开始时间
        if($scope.filterStart != "-1" ){
            var startTimeMin = get_unix_time() - parseInt($scope.filterStart) * 60
            if( startTimeMin != null ) where = where + ' and startedTime > ' + startTimeMin;
            //暂时不加入MAX
            //var startTimeMax = get_unix_time()
            //if( startTimeMax != null ) where = where + ' and startedTime < ' + startTimeMax;
        }
        if($scope.filterEnd != "-1" ){
            var finishTimeMin = get_unix_time() - parseInt($scope.filterEnd) * 60
            if( finishTimeMin != null ) where = where + ' and finishedTime > ' + finishTimeMin;
            //暂时不加入finishTimeMax
            // var finishTimeMax = get_unix_time()
        }
        return where
    }

    $scope.changeOrder=function(key){
        if($scope.orderField == key){
            if($scope.orderDirection=="asc"){
                $scope.orderDirection="desc"
            }
            else{
                $scope.orderDirection="asc"
            }
        }
        else{
            $scope.orderField = key
        }
        $scope.loadAppList()
    }

    $scope.setMaxPage=function(sum){
        $scope.maxPage = Math.floor((parseInt(sum)-1)/50)+1
    }

    $scope.prePage=function(){
        if($scope.nowPage == 1) return;
        $scope.setPage($scope.nowPage - 1)
    }

    $scope.nextPage=function(){
        if( $scope.nowPage == $scope.maxPage) return;
        $scope.setPage($scope.nowPage + 1)  
    }

    $scope.setPage=function(want){
        if(want<1 || want>$scope.maxPage) return;
        $scope.nowPage=want;
        if( $scope.nowPage == 1 ) $scope.pre=false
        else $scope.pre=true
        if( $scope.nowPage == $scope.maxPage) $scope.next=false
        else $scope.next=true
        $scope.loadAppList()
    }

    $scope.init = function(){
        //init var below
        $scope.appkeyList = ["mapsTotal","mapsPending","mapsRunning","failedMapAttempts","killedMapAttempts","successfulMapAttempts","reducesTotal","reducesPending","reducesRunning","failedReduceAttempts","killedReduceAttempts","successfulReduceAttempts"];
        $scope.app_state = {}
        $scope.appsum={}
        $scope.has_query = false
        //$(".form_datetime").datetimepicker({format: 'yyyy-mm-dd hh:ii'})
        
        //init filter value
        $scope.filterEnd = "1440"
        $scope.filterStart = -1
        $scope.orderField="appid"
        $scope.orderDirection="desc"
        $scope.limit=50
        $scope.nowPage=1
        $scope.maxPage=1
        
        //init rm params
        $scope.selected_rm_fields=["app","map","reduce"]
        $scope.rm_fields= {app:"App状况",map:"Map状况",reduce:"Reduce状况",file:"中间文件读写",hdfs:"HDFS读写"};
        $scope.rm_time=1440
        $scope.rm_split=60
        
        //init nm params
        $rootScope.myHttp('GET', '/monitorback/job_query_init_info', {}, 
            function(res){
                $scope.nm_hosts           = res.data.nm_hosts;
                $scope.selected_nm_hosts  = $scope.nm_hosts.slice(0,Math.min(3,$scope.nm_hosts.length));
                $scope.selected_nm_fields = ["containerNum","amNum"];
                $scope.nm_fields          = {containerNum:"Container数量",amNum:"AM数量",map:"Map状况",reduce:"Reduce状况",file:"中间文件读写",hdfs:"HDFS读写"};
                $scope.nm_time            = 1440;
                $scope.nm_split           = 60;

                $scope.nmQuery(); // 触发第一次查询绘图
            }
        );
       
        //init dict
        //$scope.states = ['', 'FINISHED'];
        //$scope.finalStatuss = ['', 'SUCCEEDED', 'KILLED', 'FAILED'];
        $scope.stateDict = {"FINISHED":"完成"}
        $scope.finalStatusDict = {"SUCCEEDED":"成功","KILLED":"中止","FAILED":"失败"}
        $scope.fieldDict = {
            "appid":"应用id",
            "user":"用户",
            "name":"名称",
            "queue":"队列",
            "startedTime":"开始时间",
            "finishedTime":"结束时间",
            "state":"状态",
            "finalStatus":"结果",
            "attemptNumber":"重试",
            "mapsTotal":"map数量",
            "reducesTotal":"reduce数量",
            "fileRead":"本地读大小",
            "hdfsRead":"HDFS读大小",
            "mapsTotal":"map全部",
            "mapsCompleted":"map完成",
            "localMap":"map本地",
            "reducesTotal":"reduce全部",
            "reducesCompleted":"reduce完成",
            "fileRead":"本地文件读大小",
            "fileWrite":"本地文件写大小",
            "hdfsRead":"HDFS读大小",
            "hdfsWrite":"HDFS写大小"
        }
        
        $scope.orderDict = {"desc":"降序","asc":"升序"}
        $scope.timeDict = [
            {"value":10,"dis":"最近10分钟"},
            {"value":60,"dis":"最近1小时"},
            {"value":180,"dis":"最近3小时"},
            {"value":720,"dis":"最近12小时"},
            {"value":1440,"dis":"最近24小时"},
            {"value":4320,"dis":"最近3天"},
            {"value":10080,"dis":"最近7天"}
        ];

        $scope.timeIntervalDict = [
            {"value":10,"dis":"10分钟"},
            {"value":60,"dis":"1小时"},
            {"value":180,"dis":"3小时"},
            {"value":360,"dis":"6小时"},
            {"value":1440,"dis":"24小时"}
        ];
        
        $scope.rmQuery();
        $scope.appQuery();

        //定时刷新正在运行的作业
        timer = $interval(function(){
          $scope.runningQuery();
        },10000);
    }

    // 历史查询
    $scope.metricsQuery = function(){
      //var fields = getMetricsFieldParams();
      //var recordTimeMin = getMetricsRecordTimeMinParams();
      //var recordTimeMax = getMetricsRecordTimeMaxParams();
      //var recordTimeSplit = getMetricsRecordTimeSplitParams();
      //
      //var appQuery;
      //appQuery = new XMLHttpRequest();
      //appQuery.onreadystatechange=function(){
      //  if (appQuery.readyState==4 && appQuery.status==200){
      //    showMetricsData(JSON.parse(appQuery.responseText));
      //  }
      //}
      //var url = "db/metricsQuery?fields="+fields+"&recordTimeSplit="+recordTimeSplit
      //        +"&recordTimeMax="+recordTimeMax+"&recordTimeMin="+recordTimeMin
      //appQuery.open("GET",url,true);
      //appQuery.send();
    }
    
    $scope.needKillApp = function(appId){
      $scope.needKillAppIds = [appId];
      $('#killAppIdModal').modal();
    };

    $scope.killApp = function(){
      $rootScope.myHttp('GET', '/monitorback/kill_app', {needKillAppIds:$scope.needKillAppIds}, 
        function(res){
          $scope.killAppInfos=res['data'];
          $('#killAppIdFinishModal').modal();
          $scope.runningQuery();
        }
        //,
        //function(){
        //  $scope.killAppInfo="删除失败";
        //  $('#killAppIdFinishModal').modal();
        //}
      );
    };

    $scope.init();
}]);
