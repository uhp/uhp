


uhpApp.controller('TemplateCtrl',['$scope','$rootScope','$http',function($scope,$rootScope,$http){
	$rootScope.menu="admin";
	$rootScope.submenu="template";	
	$scope.nowdir = "";
	$scope.nowfile = "";
	$scope.initTemplateList=function(){
		$http({
	        method: 'GET',
	        url: '/adminback/template_list',
	    }).success(function(response, status, headers, config){
	        $scope.templates = response["templates"];
	        for(var dir in $scope.templates){
	        	$scope.nowdir = dir;
	        	break;
	        }
	    }).error(function(data, status) {
	    	$rootScope.alert("发送template_list请求失败");
	    });
		//加载host列表
		$http({
	        method: 'GET',
	        url: '/adminback/group_host_list'
	    }).success(function(response, status, headers, config){
	    	$scope.hosts = [];
	    	angular.forEach(response["hosts"], function(value, key) {
	    		$scope.hosts.push(value.name);
		    });
	    	$scope.nowhost=$scope.hosts[0]
	    }).error(function(data, status) {
	        $scope.status = status;
	    });
	}
	$scope.$watch("nowdir",function(newValue,oldValue){
		if(newValue!=oldValue){
			for(var index in $scope.templates[$scope.nowdir]){
        		$scope.nowfile = $scope.templates[$scope.nowdir][index];
        		break;
        	}
		}
	})
	$scope.$watch("nowfile",function(newValue,oldValue){
		$scope.initTemplateFile();
	})
	$scope.initTemplateList()
	$scope.initTemplateFile=function(){
		$scope.nowContent = "获取中 ..."
		if( $scope.nowdir == "" || $scope.nowfile=="" ) return;
		$http({
	        method: 'GET',
	        url: '/adminback/template_file',
	        params:  {
        		"dir" : $scope.nowdir,
        		"file" : $scope.nowfile
        	}
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]=="ok"){
	    		$scope.nowContent = $scope.content = response["content"];
	    		$scope.nowContentMaxRow = response["row"]+20;
	        }
	        else{
	        	$rootScope.alert("获取"+$scope.nowdir+"/"+$scope.nowfile+"文件失败:"+response["msg"]);
	        }   
	    }).error(function(data, status) {
	    	$rootScope.alert("发送template_file请求失败");
	    });
	}
	$scope.reset=function(){
		$scope.nowContent=$scope.content;
	}
	$scope.save=function(){
		if( $scope.content == $scope.nowContent) {
			$rootScope.alert("文件没有变化");
			return;
		}
		$("#templateSaveModal").modal();
		$http({
	        method: 'GET',
	        url: '/adminback/save_template_file',
	        params:  {
        		"dir" : $scope.nowdir,
        		"file" : $scope.nowfile,
        		"content" : $scope.nowContent
        	}
	    }).success(function(response, status, headers, config){
	    	$("#templateSaveModal").modal('hide');
	    	if(response["ret"] != "ok"){
	        	$rootScope.alert("获取"+$scope.nowdir+"/"+$scope.nowfile+"文件失败:"+response["msg"]);
	        }   
	    	$scope.initTemplateFile()
	    }).error(function(data, status) {
	    	$("#templateSaveModal").modal('hide');
	    	$rootScope.alert("发送save_template_file请求失败");
	    });
	}
	$scope.build=function(){
		$("#templateModal").modal();
		
		//加载对应的生成的配置文件
		$scope.buildContent="生成中 ...."
		$http({
	        method: 'GET',
	        url: '/adminback/template_build_file',
	        params:{
	        	"dir" : $scope.nowdir,
        		"file" : $scope.nowfile,
        		"host" : $scope.nowhost
	        }
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]=="ok"){
	    		$scope.buildContent = response["content"];
	    		$scope.buildContentMaxRow = response["row"]+20;
	        }
	        else{
	        	$scope.buildContent = "获取"+$scope.nowhost+"的"+$scope.nowdir+"/"+$scope.nowfile+"配置文件失败:"+response["msg"];
	        	$rootScope.alert("获取"+$scope.nowhost+"的"+$scope.nowdir+"/"+$scope.nowfile+"配置文件失败");
	        }   
	    }).error(function(data, status) {
	    	$rootScope.alert("发送template_build_file请求失败");
	    });
	}
	$scope.download=function(){
		$("#templateDownloadModal").modal();
		
		//加载对应的生成的配置文件
		$scope.downloadContent="生成中 ...."
		$http({
	        method: 'GET',
	        url: '/adminback/template_download_file',
	        params:{
	        	"dir" : $scope.nowdir,
        		"host" : $scope.nowhost
	        }
	    }).success(function(response, status, headers, config){
	    	if(response["ret"]=="ok"){
	    		
	        }
	        else{
	        	$scope.downloadContent = "下载"+$scope.nowhost+"的"+$scope.nowdir+"配置文件失败:"+response["msg"];
	        	$rootScope.alert("下载"+$scope.nowhost+"的"+$scope.nowdir+"配置文件失败");
	        }   
	    }).error(function(data, status) {
	    	$rootScope.alert("发送template_download_file请求失败");
	    });
	} 
}]);
