/*
 * Define nipapApp angular application
 */
var nipapApp = angular.module('nipapApp', [
	'ngRoute',
	'ui.bootstrap',
	'ngTagsInput',
	'nipapApp.controllers',
	'nipapApp.directives',
	'nipapApp.filters',
	'nipapApp.services'
]);

/*
 * App configuration
 */
nipapApp.config(function($routeProvider, $uibTooltipProvider, $sceProvider, $locationProvider) {

		/*
		 * Define application routes
		 */
		$routeProvider
			.when('/pool/add', {
				'controller': 'PoolAddController',
				'templateUrl': '/templates/pool_add.html'
			})
			.when('/pool/edit/:pool_id', {
				'controller': 'PoolEditController',
				'templateUrl': '/templates/pool_edit.html'
			})
			.when('/pool/list', {
				'controller': 'PoolListController',
				'templateUrl': '/templates/pool_list.html'
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
			})
			.when('/vrf/list', {
				'controller': 'VRFListController',
				'templateUrl': '/templates/vrf_list.html'
			});

		/*
		 * Default options for tooltips
		 */
		$uibTooltipProvider
			.options({
				'placement': 'bottom',
				'popupDelay': 100
			});

		/*
		 * Disable Strict Contextual Escaping on the application. At
		 * this stage where the application is partly implemented
		 * outside AngularJS but still using AngularJS directives, it's
		 * really difficult to get things to work with the SCE feature
		 * enabled. Re-enable again when more of the application is
		 * implemented in AngularJS.
		 */
		$sceProvider.enabled(false);

		/*
		 * Remove default hash prefix ("!") introduced in AngularJS 1.6
		 */
		$locationProvider.hashPrefix("");

});
