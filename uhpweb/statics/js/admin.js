//use base.js
var uhpApp = angular.module('uhpApp', ['ngRoute', 'ngAnimate', 'ngSanitize','angularFileUpload','ui.bootstrap']);
//,'ui.bootstrap'
//'$cookiesProvider',
//,'localytics.directives'
uhpApp.config(['$routeProvider', "$interpolateProvider",'$rootScopeProvider', function($routeProvider, $interpolateProvider,$rootScopeProvider) {
	$interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
    $routeProvider
    	.when('/admin-service',
        {
            controller: 'ServiceCtrl',
            templateUrl: '/statics/partials/admin/service.html'
        })
        .when('/admin-host',
        {
            controller: 'HostsCtrl',
            templateUrl: '/statics/partials/admin/host.html'
        })
        .when('/admin-task',
        {
            controller: 'TaskCtrl',
            templateUrl: '/statics/partials/admin/task.html'
        })
        .when('/admin-setting',
        {
            controller: 'SettingCtrl',
            templateUrl: '/statics/partials/admin/setting.html'
        })
        .when('/admin-template',
        {
            controller: 'SettingCtrl',
            templateUrl: '/statics/partials/admin/template.html'
        })
        .when('/admin-jar',
        {
            controller: 'JarCtrl',
            templateUrl: '/statics/partials/admin/jar.html'
        })
        .when('/admin-manual',
        {
            controller: 'ManualCtrl',
            templateUrl: '/statics/partials/admin/manual.html'
        })
        .when('/monitor', {
            redirectTo: '/monitor/overview'
        })
        .when('/monitor/overview', {
            controller: 'MoniOverviewCtrl',
            templateUrl: '/statics/partials/monitor/monitor.html'
        })
        .when('/monitor/host', {
            controller: 'MoniHostCtrl',
            templateUrl: '/statics/partials/monitor/monitor.html'
        })
        .when('/monitor/service', {
            controller: 'MoniServiceCtrl',
            templateUrl: '/statics/partials/monitor/monitor.html'
        })
        .when('/monitor/job', {
            controller: 'MoniJobCtrl',
            templateUrl: '/statics/partials/monitor/monitor.html'
        })
        .when('/monitor/conf', {
            controller: 'MoniConfCtrl',
            templateUrl: '/statics/partials/monitor/monitor.html'
        })
        .otherwise({ redirectTo: '/admin-service' });

}]);

uhpApp.service('anchorSmoothScroll', function(){
    
    this.scrollTo = function(eID) {

        // This scrolling function 
        // is from http://www.itnewb.com/tutorial/Creating-the-Smooth-Scroll-Effect-with-JavaScript
        
        var startY = currentYPosition();
        var stopY = elmYPosition(eID);
        var distance = stopY > startY ? stopY - startY : startY - stopY;
        if (distance < 100) {
            scrollTo(0, stopY); return;
        }
        var speed = Math.round(distance / 100);
        if (speed >= 20) speed = 20;
        var step = Math.round(distance / 25);
        var leapY = stopY > startY ? startY + step : startY - step;
        var timer = 0;
        if (stopY > startY) {
            for ( var i=startY; i<stopY; i+=step ) {
                setTimeout("window.scrollTo(0, "+leapY+")", timer * speed);
                leapY += step; if (leapY > stopY) leapY = stopY; timer++;
            } return;
        }
        for ( var i=startY; i>stopY; i-=step ) {
            setTimeout("window.scrollTo(0, "+leapY+")", timer * speed);
            leapY -= step; if (leapY < stopY) leapY = stopY; timer++;
        }
        
        function currentYPosition() {
            // Firefox, Chrome, Opera, Safari
            if (self.pageYOffset) return self.pageYOffset;
            // Internet Explorer 6 - standards mode
            if (document.documentElement && document.documentElement.scrollTop)
                return document.documentElement.scrollTop;
            // Internet Explorer 6, 7 and 8
            if (document.body.scrollTop) return document.body.scrollTop;
            return 0;
        }
        
        function elmYPosition(eID) {
            var elm = document.getElementById(eID);
            var y = elm.offsetTop;
            var node = elm;
            while (node.offsetParent && node.offsetParent != document.body) {
                node = node.offsetParent;
                y += node.offsetTop;
            }
            //return y;
            return y - 70; // 页面上导航高度
        }

    };
    
});

