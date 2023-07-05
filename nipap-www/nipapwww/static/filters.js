/*
 * Filters for the NIPAP AngularJS app
 */

var nipapAppFilters = angular.module('nipapApp.filters', []);

/*
 * Filter to return number of entries in 'dict', ie JavaScript Object
 */
nipapAppFilters.filter('dictSize', function () {
	return function(object) {
		return Object.keys(object).length;
	}
});


/*
 * Filter to return number of entries in 'dict', ie JavaScript Object
 */
nipapAppFilters.filter('notEmpty', function () {
	return function(object) {
		return !!(object && Object.keys(object).length);
	};
});


/*
 * Filter to format tags for tag popover
 */
nipapAppFilters.filter('popoverFormatTags', function () {
	return function(object) {
		return '<div style="text-align: left;">Tags: <br/>' + Object.keys(object).join('<br/>') + '</div>';
	};
});
