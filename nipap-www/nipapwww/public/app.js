/*
 * Define nipapApp angular application
 */
var nipapApp = angular.module('nipapApp', [
	'ngRoute',
	'ui.bootstrap',
	'ngTagsInput',
	'nipapApp.controllers',
	'nipapApp.directives',
	'nipapApp.filters'
]);

/*
 * App configuration
 */
nipapApp.config(['$routeProvider',
	function($routeProvider) {
		$routeProvider.
			when('/prefix/add/from_pool', {
				'controller': 'AddPrefixFromPoolController'
			}).
			when('/prefix/add/from_pool/:pool_id', {
				'controller': 'AddPrefixFromPoolController'
			})

}]);
