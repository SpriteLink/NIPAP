/*
 * Controllers for the NIPAP AngularJS app
 */

/*
 * Define nipapApp angular application
 */
var nipapApp = angular.module('nipapApp', [ 'ui.bootstrap.dropdownToggle' ]);

/*
 * VRFListController - used to list VRFs on the /vrf/list-page
 */
nipapApp.controller('VRFListController', function ($scope, $http) {

	// Fetch VRFs from backend
	$http.get('/xhr/list_vrf').success(function (data) {
		if (data.hasOwnProperty('error')) {
			// display some error message
		} else {
			$scope.vrfs = data;
		}
	});


	/*
	 * Callback function after a vrf has been removed
	 */
	$scope.vrfRemoved = function (data, vrf) {

		if ('error' in data) {
			showDialogNotice('Error', data.message);
			return;
		}

		var index = $scope.vrfs.indexOf(vrf);
		$scope.vrfs.splice(index, 1);

	}


	/*
	 * Display remove confirmation dialog
	 */
	$scope.vrfConfirmRemove = function (evt, vrf) {
		evt.preventDefault();
		var dialog = showDialogYesNo('Really remove VRF?', 'Are you sure you want to remove the VRF "' + vrf.rt + '"?',
		function () {
			var data = {
				'id': vrf.id
			};
			$http.get('/xhr/remove_vrf', { 'params': data })
				.success(function (data) {
					$scope.vrfRemoved(data, vrf);
				})
				.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
				});

			dialog.dialog('close');

		});
	}
});
