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
nipapApp.config(function($routeProvider, $tooltipProvider) {

		/*
		 * Define application routes
		 */
		$routeProvider
			.when('/pool/add', {
				'controller': 'PoolAddController',
				'templateUrl': '/templates/pool_add.html'
			})
			.when('/prefix/add/:allocation_method/:allocation_method_parameter?', {
				'controller': 'PrefixAddController',
				'templateUrl': '/templates/prefix_add.html'
			})
			.when('/prefix/edit/:prefix_id', {
				'controller': 'PrefixEditController',
				'templateUrl': '/templates/prefix_edit.html'
			})
			.when('/vrf/add', {
				'controller': 'VRFAddController',
				'templateUrl': '/templates/vrf_add.html'
			})
			.when('/vrf/edit/:vrf_id', {
				'controller': 'VRFEditController',
				'templateUrl': '/templates/vrf_edit.html'
			});

		/*
		 * Default options for tooltips
		 */
		$tooltipProvider
			.options({
				'placement': 'bottom',
				'popupDelay': 100
			});
});
