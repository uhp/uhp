
uhpApp.controller('JarCtrl',['$scope','$rootScope','$http','$fileUploader',function($scope,$rootScope,$http,$fileUploader){
	$rootScope.menu="admin";
	$rootScope.submenu="jar";	

    // create a uploader with options
    var uploader = $scope.uploader = $fileUploader.create({
        scope: $scope,                          // to automatically update the html. Default: $rootScope
        url: 'adminback/aux_upload',
        formData: [
            { key: 'value' }
        ],
        filters: [
            function (item) {                    // first user filter
                console.log(item);
                console.info('filter1');
                return true;
            }
        ]
    });


    // FAQ #1
    var item = $scope.item = {
        file: {
            name: 'Previously uploaded file',
            size: 1e6
        },
        progress: 100,
        isUploaded: true,
        isSuccess: true
    };
    $scope.item.remove = function() {
        uploader.removeFromQueue(this);
    };
    uploader.queue.push(item);
    uploader.progress = 100;


    // ADDING FILTERS

    uploader.filters.push(function (item) { // second user filter
        console.info('filter2');
        return true;
    });

    // REGISTER HANDLERS

    uploader.bind('afteraddingfile', function (event, item) {
        console.info('After adding a file', item);
    });

    uploader.bind('whenaddingfilefailed', function (event, item) {
        console.info('When adding a file failed', item);
    });

}]);
