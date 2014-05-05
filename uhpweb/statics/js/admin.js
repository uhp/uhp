//use base.js
var uhpApp = angular.module('uhpApp', ['ngRoute', 'ngAnimate', 'ui.bootstrap', 'ngSanitize']);
//,'ui.bootstrap'
//'$cookiesProvider',
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
            templateUrl: '/statics/partials/monitor/overview.html'
        })
        .when('/monitor/host', {
            controller: 'MoniHostCtrl',
            templateUrl: '/statics/partials/monitor/host.html'
        })
        .when('/monitor/service', {
            controller: 'MoniServiceCtrl',
            templateUrl: '/statics/partials/monitor/service.html'
        })
        .when('/monitor/job', {
            controller: 'MoniJobCtrl',
            templateUrl: '/statics/partials/monitor/job.html'
        })
        .when('/monitor/conf', {
            controller: 'MoniConfCtrl',
            templateUrl: '/statics/partials/monitor/conf.html'
        })
        .otherwise({ redirectTo: '/admin-service' });

}]);






