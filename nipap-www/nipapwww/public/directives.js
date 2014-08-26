/*
 * Directives for the NIPAP AngularJS app
 */

var nipapAppDirectives = angular.module('nipapApp.directives', []);

nipapAppDirectives.directive('nipapPoolSelector', function ($http) {

    return {
        restrict: 'AE',
        templateUrl: '/templates/pool_selector.html',
        link: function (scope, elem, attrs) {
            // Fetch Pools from backend
            $http.get('/xhr/list_pool').success(function (data) {
                if (data.hasOwnProperty('error')) {
                    // TODO: display some error message
                } else {
                    scope.pools = data;
                }
            });
        }
    };

});

nipapAppDirectives.directive('nipapVRFSelector', function ($http) {

    return {
        restrict: 'AE',
        templateUrl: ''
    };

});
