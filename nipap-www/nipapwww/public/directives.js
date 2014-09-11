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

nipapAppDirectives.directive('nipapVrfSelector', function ($http, $timeout) {

	return {
		restrict: 'AE',
		templateUrl: '/templates/vrf_selector.html',
		scope: {
			selected_vrf: '=selectedVrf'
		},
		link: function (scope, elem, attr) {

			scope.query_string = '';
			scope.timeout_promise = null;
			scope.search_result = [];
			scope.selected_vrf = null;
			scope.query_id = 0;
			scope.internal_seleted_vrf = scope.selected_vrf || { 'id': null };

			/*
			 * Function ran when VRF search query string has changed
			 */
			scope.vrfQueryStringChanged = function () {
				// cancel earlier timeout if it exists
				if (scope.timeout_promise !== null) {
					$timeout.cancel(scope.timeout_promise);
				}
				scope.timeout_promise = $timeout(scope.performVRFSearch, 200);
			}

			/*
			 * Perform VRF search
			 */
			scope.performVRFSearch = function () {

				var search_q = {
					'query_id': scope.query_id,
					'query_string': $.trim(scope.query_string),
					'max_result': 10,
					'offset': 0
				};

				// If search string empty, search for default VRF
				if (search_q['query_string'] == '') {
					search_q['vrf_id'] = 0;
				}

				$http.get('/xhr/smart_search_vrf', { 'params': search_q })
					.success(scope.receiveVRFSearchResult)
					.error(function (data, stat) {
						var msg = data || "Unknown failure";
						showDialogNotice('Error', stat + ': ' + msg);
					});

				scope.query_id += 1;

			}

			/*
			 * Search result returned
			 */
			scope.receiveVRFSearchResult = function (data) {
				if (data.hasOwnProperty('error')) {
					showDialogNotice('Error', data.message);
					return;
				}

				// Verify that received response is for latest query
				if (parseInt(data.search_options.query_id) != scope.query_id - 1) {
					return;
				}

				scope.search_result = data.result;

			}

			/*
			 * A VRF is selected
			 */
			scope.selectVRF = function (vrf) {

				// set VRF
				scope.selected_vrf = vrf;

				// TODO: close selector box

			}
		}
	};

});
