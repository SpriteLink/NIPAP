/*
 * Controllers for the NIPAP AngularJS app
 */

var nipapAppControllers = angular.module('nipapApp.controllers', []);

/*
 * VRFListController - used to list VRFs on the /vrf/list-page
 */
nipapAppControllers.controller('VRFListController', function ($scope, $http) {

	// Fetch VRFs from backend
	$http.get('/xhr/list_vrf')
        .success(function (data) {
            if (data.hasOwnProperty('error')) {
			    showDialogNotice('Error', data.message);
            } else {
                $scope.vrfs = data;
            }
        })
        .error(function (data, stat) {
            var msg = data || "Unknown failure";
            showDialogNotice('Error', stat + ': ' + msg);
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
                    if (data.hasOwnProperty('error')) {
                        showDialogNotice('Error', data.message);
                    } else {
                        $scope.vrfRemoved(data, vrf);
                    }
				})
				.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
				});

			dialog.dialog('close');

		});
	}
});


/*
 * PoolListController - used to list pools on the /pool/list-page
 */
nipapAppControllers.controller('PoolListController', function ($scope, $http) {

	// Fetch Pools from backend
	$http.get('/xhr/list_pool')
        .success(function (data) {
            if (data.hasOwnProperty('error')) {
                showDialogNotice('Error', data.message);
            } else {
                $scope.pools = data;
            }
        })
        .error(function (data, stat) {
            var msg = data || "Unknown failure";
            showDialogNotice('Error', stat + ': ' + msg);
        });

	/*
	 * Callback function after a pool has been removed
	 */
	$scope.poolRemoved = function (data, pool) {

		if ('error' in data) {
			showDialogNotice('Error', data.message);
			return;
		}

		var index = $scope.pools.indexOf(pool);
		$scope.pools.splice(index, 1);

	}


	/*
	 * Display remove confirmation dialog
	 */
	$scope.poolConfirmRemove = function (evt, pool) {
		evt.preventDefault();
		var dialog = showDialogYesNo('Really remove pool?', 'Are you sure you want to remove the pool "' + pool.name + '"?',
		function () {
			var data = {
				'id': pool.id
			};
			$http.get('/xhr/remove_pool', { 'params': data })
				.success(function (data) {
					$scope.poolRemoved(data, pool);
				})
				.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
				});

			dialog.dialog('close');

		});
	}
});

/*
 * PrefixAddController - Used to add prefixes to NIPAP
 */
nipapAppControllers.controller('PrefixAddController', function ($scope, $http) {

    $scope.prefix_alloc_method = null;
    $scope.from_pool = null;
    $scope.from_prefix = null;

    $scope.pool_has_default_preflen = null;
    $scope.pool_use_default_preflen = true;
    $scope.pool_preflen = null;

    $scope.type_input_enabled = true;

    $scope.prefix_family = 6;
    $scope.prefix_length = null;

    $scope.vrf = null;

	$scope.prefix = {
		prefix: null,
		vrf: null,
		description: null,
		comment: null,
		node: null,
		tags: [],
		inherited_tags: [],
		type: null,
		country: null,
		order_id: null,
		customer_id: null,
		vlan: null,
		monitor: false,
		alarm_priority: null
	};

    /*
     * Watch for change to 'from_pool'-variable
     */
    $scope.$watchCollection('[ from_pool, prefix_family ]', function(newValue, oldvalue){

        if ($scope.from_pool !== null) {
            $scope.prefix_type = $scope.from_pool.default_type;
            $scope.type_input_enabled = false;

            var def_preflen;

            if ($scope.prefix_family == "4") {
                def_preflen = "ipv4_default_prefix_length";
            } else {
                def_preflen = "ipv6_default_prefix_length";
            }

            if ($scope.from_pool[def_preflen] !== null) {
                $scope.pool_has_default_preflen = true;
                $scope.pool_preflen = $scope.from_pool[def_preflen];
                $scope.prefix_length = $scope.from_pool[def_preflen];
            }

            if ($scope.from_pool.vrf_id !== null) {
                // fetch VRF data for pool's implied VRF
                $http.get('', { 'params': {
                    'vrf_id': $scope.from_pool.vrf_id,
                    'query_string': ''
                } })
				.success(function (data) {
                    if (data.hasOwnProperty('error')) {
                        showDialogNotice('Error', data.message);
                    } else {
                        $scope.vrf = data.result[0];
                    }
				})
				.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
				});
            }
        }
    });


	/*
	 * Add prefix to NIPAP
	 */
	$scope.addPrefix = function () {

	}

});
