/*
 * Directives for the NIPAP AngularJS app
 */

var nipapAppDirectives = angular.module('nipapApp.directives', []);

nipapAppDirectives.directive('nipapPoolSelector', function ($http) {

	return {
		restrict: 'AE',
		templateUrl: '/templates/pool_selector.html',
		scope: {
			selected_pool: '=selectedPool'
		},
		link: function (scope, elem, attrs) {
			// Fetch Pools from backend
			$http.post('/xhr/list_pool',
				JSON.stringify({}),
				{ 'headers': { 'Content-Type': 'application/json' } })
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						scope.pools = response.data;
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
				});

			/*
			 * A pool is selected
			 */
			scope.selectPool = function (pool) {
				scope.selected_pool = pool;
			}
		}
	};

});

nipapAppDirectives.directive('nipapPoolSelectorPopup', function ($http, $timeout) {

	return {
		restrict: 'AE',
		templateUrl: '/templates/pool_selector_popup.html',
		scope: {
			selected_pool: '=selectedPool'
		},
		link: function (scope, elem, attr) {

			scope.query_string = '';
			scope.pools = [];
			scope.query_id = 0;
			scope.popup_open = false;

			/*
			 * Fetch pools
			 */
			$http.post('/xhr/list_pool',
				JSON.stringify({}),
				{ 'headers': { 'Content-Type': 'application/json' } })
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						scope.pools = response.data;
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
				});

			/*
			 * A pool is selected
			 */
			scope.selectPool = function (pool) {

				// Set pool & close popup
				scope.selected_pool = pool;
				scope.popup_open = false;

			}

			scope.deselectPool = function (pool) {
				// deselect pool & close popup
				scope.selected_pool = null;
				scope.pools = [];
				scope.popup_open = false;
			}

			/*
			 * Run when popup menu is toggled
			 */
			scope.toggled = function (open) {
				if (open) {
					// If menu was opened, place focus on text input field
					$timeout(function () {
						$('input[name="pool_search_string"]').focus();
					});
				}
			}
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
			scope.query_id = 0;
			scope.popup_open = false;

			/*
			 * Function to run when VRF search query string has changed.
			 * Waits 200 ms for further changes to the query string to let the
			 * user finish typing before sending the query.
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

				$http.post('/xhr/smart_search_vrf',
					JSON.stringify(search_q),
					{ 'headers': { 'Content-Type': 'application/json' } })
					.then(function (response) {
						scope.receiveVRFSearchResult(response.data);
					})
					.catch(function (response) {
						var msg = response.data || "Unknown failure";
						showDialogNotice('Error', response.status + ': ' + msg);
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

				// set VRF & close popup
				scope.selected_vrf = vrf;
				scope.popup_open = false;

			}

			/*
			 * Run when popup menu is toggled
			 */
			scope.toggled = function (open) {
				if (open) {
					// If menu was opened, place focus on text input field
					$timeout(function () {
						$('input[name="vrf_search_string"]').focus();
					});
				}
			}

			// Perform search (with empty query string) to fetch default VRF
			scope.performVRFSearch();

		}
	};
});
