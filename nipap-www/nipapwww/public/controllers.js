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
nipapAppControllers.controller('PrefixAddController', function ($scope, $routeParams, $http) {

	// prefix method is add - used to customize prefix form template
	$scope.method = 'add';

	$scope.prefix_alloc_method = null;
	// Set to true if allocation method was provided in URL
	$scope.prefix_alloc_method_provided = false;

	$scope.from_pool = null;
	// Set to true if the pool to allocate from was provided in the URL
	$scope.from_pool_provided = false;

	$scope.from_prefix = null;
	// Set to true if the prefix to allocate from was provided in the URL
	$scope.from_prefix_provided = false;

	// Set to true if pool has a default prefix length for current address family
	$scope.pool_has_default_preflen = false;

	// Keep track on whether the user wants to use the pool's default prefix
	// length or not
	$scope.pool_use_default_preflen = true;
	$scope.pool_default_preflen = null;

	// Keep track of whether the user has chosen to enable the prefix type
	// input fields, when allocating prefix from a pool (ie. to not use the
	// pool's default prefix type)
	$scope.display_type_input_pool = false;

	$scope.prefix_family = 4;
	$scope.prefix_length = null;

	$scope.vrf = null;

	$scope.prefix = {
		prefix: null,
		status: 'assigned',
		description: null,
		comment: null,
		node: null,
		tags: [],
		type: null,
		country: null,
		order_id: null,
		customer_id: null,
		vlan: null,
		monitor: false,
		alarm_priority: null
	};

	// List of prefixes added to NIPAP
	$scope.added_prefixes = [];

	/*
	 * Handle route parameters (extracted from the URL)
	 */
	// Is allocation method set?
	if ($routeParams.hasOwnProperty('allocation_method')) {
		$scope.prefix_alloc_method = $routeParams.allocation_method;
		$scope.prefix_alloc_method_provided = true;
	}

	// Did we get any allocation parameters (pool ID or prefix ID)?
	if ($routeParams.hasOwnProperty('allocation_method_parameter')) {

		var allocation_parameter = parseInt($routeParams.allocation_method_parameter);

		if ($scope.prefix_alloc_method == 'from-pool') {

			// Allocation method parameter is pool ID - fetch pool
			$scope.from_pool_provided = true;
			$http.get('/xhr/list_pool', { 'params': { 'id': allocation_parameter } })
				.success(function (data) {
					if (data.hasOwnProperty('error')) {
						showDialogNotice('Error', data.message);
					} else {
						$scope.from_pool = data[0];
					}
				})
				.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
				});

		} else if ($scope.prefix_alloc_method == 'from-prefix') {

			// Allocation method parameter is prefix ID - fetch prefix
			$scope.from_prefix_provided = true;
			$http.get('/xhr/list_prefix', { 'params': { 'id': allocation_parameter } })
				.success(function (data) {
					if (data.hasOwnProperty('error')) {
						showDialogNotice('Error', data.message);
					} else {
						$scope.from_prefix = data[0];
					}
				})
				.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
				});
		}
	}

	/*
	 * Watch for change to 'from_pool' and 'prefix_family' variables
	 */
	$scope.$watchCollection('[ from_pool, prefix_family ]', function(newValue, oldValue){

		if ($scope.from_pool !== null) {

			// We're allocating from a pool - reset from_prefix
			$scope.from_prefix = null;

			if ($scope.from_pool.default_type !== null) {
				$scope.prefix.type = $scope.from_pool.default_type;
				$scope.display_type_input_pool = false;
			} else {
				$scope.display_type_input_pool = true;
			}

			// Extract default prefix length for selected address family
			var def_preflen;
			if ($scope.prefix_family == "4") {
				def_preflen = "ipv4_default_prefix_length";
			} else {
				def_preflen = "ipv6_default_prefix_length";
			}

			if ($scope.from_pool[def_preflen] !== null) {
				$scope.pool_has_default_preflen = true;
				$scope.pool_default_preflen = $scope.from_pool[def_preflen];
				$scope.prefix_length = $scope.from_pool[def_preflen];
			} else {
				$scope.pool_has_default_preflen = false;
				$scope.pool_default_preflen = null;
				$scope.pool_use_default_preflen = false;
				$scope.prefix_length = null;
			}

			if ($scope.from_pool.vrf_id !== null) {
				// fetch VRF data for pool's implied VRF
				$http.get('/xhr/smart_search_vrf',
					{ 'params': {
						'vrf_id': $scope.from_pool.vrf_id,
						'query_string': ''
				}})
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
			} else {
				// Pool is missing implied VRF - means the pool is empty!
				$scope.vrf = null;
			}
		}
	});

	/*
	 * Watch for changes to the 'from_prefix' variable
	 */
	$scope.$watch('from_prefix', function() {

		if ($scope.from_prefix !== null) {

			// We're allocating from a prefix - reset from_pool
			$scope.from_pool = null;

			// Fetch prefix's VRF
			$http.get('/xhr/smart_search_vrf',
				{ 'params': {
					'vrf_id': $scope.from_prefix.vrf_id,
					'query_string': ''
			}})
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

			// If we're allocating from an assignment, set prefix type to host
			// and prefix length to max prefix length for the selected address family.
			if ($scope.from_prefix.type == 'assignment') {
				$scope.prefix.type = 'host';
				if ($scope.from_prefix.family == 4) {
					$scope.prefix_length = 32;
				} else {
					$scope.prefix_length = 128;
				}
			}
		}
	});


	/*
	 * Submit prefix form - add prefix to NIPAP
	 */
	$scope.submitForm = function () {

		/*
		 * Create object specifying prefix attributes and how it should be
		 * added. For simplicity, we start with a copy of the prefix object
		 * from the scope and add/remove attributes according to what's
		 * required by the different allocation methods.
		 */
		var query_data = angular.copy($scope.prefix);

		// Tags & VRFs are needed no matter allocation method
		query_data.tags = JSON.stringify($scope.prefix.tags.map(function (elem) { return elem.text; }));
		if ($scope.vrf != null) {
			query_data.vrf = $scope.vrf.id;
		}

		if ($scope.prefix_alloc_method == 'from-pool') {

			// Allocation from pool requires prefix length, family and pool to
			// allocate from. Prefix not needed.
			delete query_data.prefix;
			query_data.family = $scope.prefix_family;
			if ($scope.pool_use_default_preflen) {
				query_data.prefix_length = $scope.pool_default_preflen;
			} else {
				query_data.prefix_length = $scope.prefix_length;
			}
			query_data.from_pool = $scope.from_pool.id;

		} else if ($scope.prefix_alloc_method == 'from-prefix') {

			// Allocation from prefix requires prefix length and prefix to
			// allocate from. Prefix not needed.
			delete query_data.prefix;
			query_data.prefix_length = $scope.prefix_length;
			query_data['from_prefix[]'] = $scope.from_prefix.prefix;

		}

		// Send query!
		$http.get('/xhr/add_prefix', { 'params': query_data })
			.success(function (data){
				if (data.hasOwnProperty('error')) {
					showDialogNotice('Error', data.message);
				} else {
					$scope.added_prefixes.push(data);
				}
			})
			.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
			});

	}

});

/*
 * PrefixEditController - used to edit prefixes
 */
nipapAppControllers.controller('PrefixEditController', function ($scope, $routeParams, $http) {

	// Prefix method is edit - used to customize prefix form template
	$scope.method = 'edit';

	$scope.vrf = null;

	// The tags-attributes needs to be initialized due to bug,
	// see https://github.com/mbenford/ngTagsInput/issues/204
	$scope.prefix = { 'tags': [], 'inherited_tags': [] };

	$scope.edited_prefixes = [];

	// Fetch prefix to edit from backend
	$http.get('/xhr/list_prefix', { 'params': { 'id': $routeParams.prefix_id } })
		.success(function (data) {
			if (data.hasOwnProperty('error')) {
				showDialogNotice('Error', data.message);
			} else {
				pref = data[0];

				// Tags needs to be mangled for use with tags-input
				// TODO: When all interaction with prefix add & edit functions
				// are moved to AngularJS, change XHR functions to use the same
				// format as tags-input
				pref.tags = Object.keys(pref.tags).map(function (elem) { return { 'text': elem }; } );
				pref.inherited_tags = Object.keys(pref.inherited_tags).map(function (elem) { return { 'text': elem }; } );

				$scope.prefix = pref;

				// Fetch prefix's VRF
				$http.get('/xhr/smart_search_vrf',
					{ 'params': {
						'vrf_id': $scope.prefix.vrf_id,
						'query_string': ''
				}})
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

				// Display statistics
				// TODO: Do in AngularJS-way, probably easiest to encapsulate
				// in a directive
				var data_prefix_addresses = [
					{
						value: $scope.prefix.used_addresses,
						color: '#d74228',
						highlight: '#e74228',
						label: 'Used'
					},
					{
						value: $scope.prefix.free_addresses,
						color: '#368400',
						highlight: '#36a200',
						label: 'Free'
					}
				];


				var options = { animationSteps : 20, animationEasing: "easeOutQuart" };
				var chart_prefix_addresses = new Chart($("#canvas_prefix_addresses")[0].getContext("2d")).Doughnut(data_prefix_addresses, options);

			}

		})
		.error(function (data, stat) {
			var msg = data || "Unknown failure";
			showDialogNotice('Error', stat + ': ' + msg);
		});

	/*
	 * Form submitted
	 */
	$scope.submitForm = function () {

		// If prefix is owned by other system, ask user to veryfy the changes
		if ($scope.prefix.authoritative_source != 'nipap') {
			// TODO: Replace with AngularJS-style widget
			showDialogYesNo(
				'Confirm prefix edit',
				'The prefix ' + $scope.prefix.authoritative_source + ' is managed by ' +
				'\'' + $scope.prefix.authoritative_source + '\'.<br><br>' +
				'Are you sure you want to edit it?',
				function() {
					$scope.savePrefix();
					$(this).dialog("close");
				}

			);
		} else {
			$scope.savePrefix();
		}

	}

	/*
	 * Save changes made to prefix
	 */
	$scope.savePrefix = function() {

		// Create new object with prefix data
		var prefix_data = angular.copy($scope.prefix);

		// Mangle tags
		prefix_data.tags = JSON.stringify($scope.prefix.tags.map(function (elem) { return elem.text; }));

		// Send query!
		$http.get('/xhr/edit_prefix/' + $scope.prefix.id, { 'params': prefix_data })
			.success(function (data){
				if (data.hasOwnProperty('error')) {
					showDialogNotice('Error', data.message);
				} else {
					$scope.edited_prefixes.push(data);
				}
			})
			.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
			});

	}

});

/*
 * VRFAddController - used to add VRFs
 */
nipapAppControllers.controller('VRFAddController', function ($scope, $http) {

	$scope.method = 'add';
	$scope.added_vrfs = [];

	$scope.vrf = {
		'rt': null,
		'name': null,
		'description': null,
		'tags': [],
		'avps': []
	};

	// add another empty "extra attribute" (AVP) input row
	$scope.addAvp = function() {
		$scope.vrf.avps.push({ 'attribute': '', 'value': '' });
	}

	// remove AVP row
	$scope.removeAvp = function(avp){
		var index = $scope.vrf.avps.indexOf(avp);
		$scope.vrf.avps.splice( index, 1 );
	};

	/*
	 * Submit VRF form - add VRF to NIPAP
	 */
	$scope.submitForm = function () {

		/*
		 * Create object specifying VRF attributes. Start with a copy of the
		 * VRF object from the scope.
		 */
		var query_data = angular.copy($scope.vrf);

		// Rewrite tags list to match what's expected by the XHR functions
		query_data.tags = JSON.stringify($scope.vrf.tags.map(function (elem) { return elem.text; }));
		query_data.avps = {};
		$scope.vrf.avps.forEach(function(avp) {
			query_data.avps[avp.attribute] = avp.value;
		});
		query_data.avps = JSON.stringify(query_data.avps);

		// Send query!
		$http.get('/xhr/add_vrf', { 'params': query_data })
			.success(function (data){
				if (data.hasOwnProperty('error')) {
					showDialogNotice('Error', data.message);
				} else {
					$scope.added_vrfs.push(data);
				}
			})
			.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
			});

	}

});

/*
 * VRFEditController - used to edit VRFs
 */
nipapAppControllers.controller('VRFEditController', function ($scope, $routeParams, $http) {

	$scope.method = 'edit';
	$scope.edited_vrfs = [];

	$scope.vrf = {
		'tags': []
	};

	// add another empty "extra attribute" (AVP) input row
	$scope.addAvp = function() {
		$scope.vrf.avps.push({ 'attribute': '', 'value': '' });
	}

	// remove AVP row
	$scope.removeAvp = function(avp){
		var index = $scope.vrf.avps.indexOf(avp);
		$scope.vrf.avps.splice( index, 1 );
	};



	// Fetch VRF to edit from backend
	$http.get('/xhr/smart_search_vrf',
		{ 'params': {
			'vrf_id': $routeParams.vrf_id,
			'query_string': ''
			}
		})
		.success(function (data) {
			if (data.hasOwnProperty('error')) {
				showDialogNotice('Error', data.message);
			} else {
				vrf = data.result[0];

				// Tags needs to be mangled for use with tags-input
				// TODO: When all interaction with prefix add & edit functions
				// are moved to AngularJS, change XHR functions to use the same
				// format as tags-input
				vrf.tags = Object.keys(vrf.tags).map(function (elem) { return { 'text': elem }; } );
				vrf.avps = Object.keys(vrf.avps).sort().map(function (key) { return { 'attribute': key, 'value': vrf.avps[key] }; } );

				$scope.vrf = vrf;

				// Display statistics
				// TODO: Do in AngularJS-way, probably easiest to encapsulate
				// in a directive
				var data_charts = [
					{
						color: '#d74228',
						highlight: '#e74228',
						label: 'Used'
					},
					{
						color: '#368400',
						highlight: '#36a200',
						label: 'Free'
					}
				];

				var data_vrf_addresses_v4 = angular.copy(data_charts);
				data_vrf_addresses_v4[0]['value'] = vrf.used_addresses_v4;
				data_vrf_addresses_v4[1]['value'] = vrf.free_addresses_v4;

				var data_vrf_addresses_v6 = angular.copy(data_charts);
				data_vrf_addresses_v6[0]['value'] = vrf.used_addresses_v6;
				data_vrf_addresses_v6[1]['value'] = vrf.free_addresses_v6;

				var options = { animationSteps : 20, animationEasing: "easeOutQuart" };
				if (vrf.num_prefixes_v4 > 0) {
					var chart_vrf_addresses_v4 = new Chart($("#canvas_vrf_addresses_v4")[0].getContext("2d")).Doughnut(data_vrf_addresses_v4, options);
				}

				if (vrf.num_prefixes_v6 > 0) {
					var chart_vrf_addresses_v6 = new Chart($("#canvas_vrf_addresses_v6")[0].getContext("2d")).Doughnut(data_vrf_addresses_v6, options);
				}

			}

		})
		.error(function (data, stat) {
			var msg = data || "Unknown failure";
			showDialogNotice('Error', stat + ': ' + msg);
		});

	/*
	 * Submit VRF form - edit VRF
	 */
	$scope.submitForm = function () {

		/*
		 * Create object specifying VRF attributes. Start with a copy of the
		 * VRF object from the scope.
		 */
		var query_data = angular.copy($scope.vrf);

		// Rewrite tags list to match what's expected by the XHR functions
		query_data.tags = JSON.stringify($scope.vrf.tags.map(function (elem) { return elem.text; }));
		query_data.avps = {};
		$scope.vrf.avps.forEach(function(avp) {
			query_data.avps[avp.attribute] = avp.value;
		});
		query_data.avps = JSON.stringify(query_data.avps);

		// Send query!
		$http.get('/xhr/edit_vrf/' + vrf.id, { 'params': query_data })
			.success(function (data){
				if (data.hasOwnProperty('error')) {
					showDialogNotice('Error', data.message);
				} else {
					$scope.edited_vrfs.push(data);
				}
			})
			.error(function (data, stat) {
					var msg = data || "Unknown failure";
					showDialogNotice('Error', stat + ': ' + msg);
			});

	}

});
