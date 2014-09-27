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
			.when('/prefix/add/:allocation_method/:allocation_method_parameter?', {
				'controller': 'PrefixAddController',
				'templateUrl': '/templates/prefix_add.html'
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
