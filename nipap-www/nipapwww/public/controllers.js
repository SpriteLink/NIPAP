/*
 * Controllers for the NIPAP AngularJS app
 */

var nipapAppControllers = angular.module('nipapApp.controllers', []);

/*
 * VRFListController - used to list VRFs on the /vrf/list-page
 */
nipapAppControllers.controller('VRFListController', function ($scope, $http) {

	// Fetch VRFs from backend
	$http.post('/xhr/list_vrf',
		JSON.stringify({}),
		{ 'headers': { 'Content-Type': 'application/json' } })
		.then(function (response) {
			if (response.data.hasOwnProperty('error')) {
				showDialogNotice('Error', response.data.message);
			} else {
				$scope.vrfs = response.data;
			}
		})
		.catch(function (response) {
			var msg = response.data || "Unknown failure";
			showDialogNotice('Error', response.status + ': ' + msg);
		});

	/*
	 * Display remove confirmation dialog
	 */
	$scope.vrfConfirmRemove = function (evt, vrf) {
		evt.preventDefault();
		var dialog = showDialogYesNo('Really remove VRF?', 'Are you sure you want to remove the VRF "' + vrf.rt + '"?',
		function () {
			$http.get('/xhr/remove_vrf/' + vrf.id)
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						var index = $scope.vrfs.indexOf(vrf);
						$scope.vrfs.splice(index, 1);

						// Update VRF filter - the removed VRF might be in the
						// VRF filter list
						$http.get('/xhr/get_current_vrfs')
							.then(function(response) { receiveCurrentVRFs(response.data); });
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
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
	$http.post('/xhr/list_pool',
		JSON.stringify({}),
		{ 'headers': { 'Content-Type': 'application/json' } })
		.then(function (response) {
			if (response.data.hasOwnProperty('error')) {
				showDialogNotice('Error', response.data.message);
			} else {
				$scope.pools = response.data;
			}
		})
		.catch(function (response) {
			var msg = response.data || "Unknown failure";
			showDialogNotice('Error', response.status + ': ' + msg);
		});

	/*
	 * Display remove confirmation dialog
	 */
	$scope.poolConfirmRemove = function (evt, pool) {
		evt.preventDefault();
		var dialog = showDialogYesNo('Really remove pool?', 'Are you sure you want to remove the pool "' + pool.name + '"?',
		function () {
			$http.get('/xhr/remove_pool/' + pool.id)
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						var index = $scope.pools.indexOf(pool);
						$scope.pools.splice(index, 1);
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
				});

			dialog.dialog('close');

		});
	}

});

/*
 * PrefixListController - Display prefix list
 */
nipapAppControllers.controller('PrefixListController', function ($scope, $uibModal) {

	/*
	 * Display a popup notice informing the user of how prefixes are added from
	 * a pool.
	 */
	$scope.showAddPrefixFromPoolNotice = function () {

		var modalInstance = $uibModal.open({
			templateUrl: 'add_prefix_from_pool_notice.html',
			windowClass: 'nipap_modal'
		});

	}

	/*
	 * Display a popup notice informing the user of how prefixes are added from
	 * a prefix.
	 */
	$scope.showAddPrefixFromPrefixNotice = function () {

		var modalInstance = $uibModal.open({
			templateUrl: 'add_prefix_from_prefix_notice.html',
			windowClass: 'nipap_modal'
		});

	}

});

/*
 * PrefixAddController - Used to add prefixes to NIPAP
 */
nipapAppControllers.controller('PrefixAddController', function ($scope, $routeParams, $http, prefixHelpers, inputValidationHelpers) {

	// prefix method is add - used to customize prefix form template
	$scope.method = 'add';

	// Expose prefixHelpers.enableNodeInput to templates
	$scope.enableNodeInput = prefixHelpers.enableNodeInput;

	// open up the datepicker
	$scope.dpOpen = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		$scope.dpOpened = !$scope.dpOpened;
	};

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

	$scope.prefix = {
		prefix: null,
		vrf: null,
		pool: null,
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
		alarm_priority: null,
		avps: []
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
			$http.post('/xhr/list_pool',
				JSON.stringify({ 'id': allocation_parameter }),
				{ 'headers': { 'Content-Type': 'application/json' } })
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						$scope.from_pool = response.data[0];
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
				});

		} else if ($scope.prefix_alloc_method == 'from-prefix') {

			// Allocation method parameter is prefix ID - fetch prefix
			$scope.from_prefix_provided = true;
			$http.post('/xhr/list_prefix',
				JSON.stringify({ 'id': allocation_parameter }),
				{ 'headers': { 'Content-Type': 'application/json' } })
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						$scope.from_prefix = response.data[0];
						$scope.prefix_family = response.data[0].family;
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
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
				$http.post('/xhr/smart_search_vrf',
					JSON.stringify({
						'vrf_id': $scope.from_pool.vrf_id,
						'query_string': ''
						}
					), {
						'headers': { 'Content-Type': 'application/json'}
					})
					.then(function (response) {
						if (response.data.hasOwnProperty('error')) {
							showDialogNotice('Error', response.data.message);
						} else {
							$scope.prefix.vrf = response.data.result[0];
						}
					})
					.catch(function (response) {
						var msg = response.data || "Unknown failure";
						showDialogNotice('Error', response.status + ': ' + msg);
					});
			} else {
				// Pool is missing implied VRF - means the pool is empty!
				$scope.prefix.vrf = null;
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
			$http.post('/xhr/smart_search_vrf',
				JSON.stringify({
					'vrf_id': $scope.from_prefix.vrf_id,
					'query_string': ''
				}), {
					'headers': { 'Content-Type': 'application/json' }
				})
				.then(function (response) {
					if (response.data.hasOwnProperty('error')) {
						showDialogNotice('Error', response.data.message);
					} else {
						$scope.prefix.vrf = response.data.result[0];
					}
				})
				.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
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

	// add another empty "extra attribute" (AVP) input row
	$scope.addAvp = function() {
		$scope.prefix.avps.push({ 'attribute': '', 'value': '' });
	}

	// remove AVP row
	$scope.removeAvp = function(avp) {
		var index = $scope.prefix.avps.indexOf(avp);
		$scope.prefix.avps.splice( index, 1 );
	}

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
		query_data.vrf = null;
		query_data.pool = null;

		// Tags, VRF and pool are needed no matter allocation method
		query_data.tags = $scope.prefix.tags.map(function (elem) { return elem.text; });
		if ($scope.prefix.vrf != null) {
			query_data.vrf = $scope.prefix.vrf.id;
		}

		if ($scope.prefix.pool != null) {
			query_data.pool = $scope.prefix.pool.id;
		}

		// Mangle avps
		query_data.avps = {};
		$scope.prefix.avps.forEach(function(avp) {
			if (avp.attribute != '' && avp.value != '') {
				query_data.avps[avp.attribute] = avp.value;
			}
		});

		// Rewrite empty VLAN to null
		query_data.vlan = inputValidationHelpers.emptyToNull($scope.prefix.vlan);

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
			query_data['from_prefix'] = [ $scope.from_prefix.prefix ];

		}

		// Send query!
		$http.post('/xhr/add_prefix',
				JSON.stringify(query_data),
				{ 'headers': { 'Content-Type': 'application/json'} })
			.then(function (response){
				if (response.data.hasOwnProperty('error')) {
					showDialogNotice('Error', response.data.message);
				} else {
					$scope.added_prefixes.push(response.data);
				}
			})
			.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
			});

	}

});

/*
 * PrefixEditController - used to edit prefixes
 */
nipapAppControllers.controller('PrefixEditController', function ($scope, $routeParams, $http, $filter, prefixHelpers, inputValidationHelpers) {

	// Prefix method is edit - used to customize prefix form template
	$scope.method = 'edit';

	// Expose prefixHelpers.enableNodeInput to templates
	$scope.enableNodeInput = prefixHelpers.enableNodeInput;

	// The tags-attributes needs to be initialized due to bug,
	// see https://github.com/mbenford/ngTagsInput/issues/204
	$scope.prefix = { 'tags': [], 'inherited_tags': [] };

	$scope.edited_prefixes = [];

	// open up the datepicker
	$scope.dpOpen = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		$scope.dpOpened = !$scope.dpOpened;
	};

	// add another empty "extra attribute" (AVP) input row
	$scope.addAvp = function() {
		$scope.prefix.avps.push({ 'attribute': '', 'value': '' });
	}

	// remove AVP row
	$scope.removeAvp = function(avp) {
		var index = $scope.prefix.avps.indexOf(avp);
		$scope.prefix.avps.splice( index, 1 );
	}

	// Fetch prefix to edit from backend
	$http.post('/xhr/list_prefix',
		JSON.stringify({ 'id': $routeParams.prefix_id }),
		{
			'headers': { 'Content-Type': 'application/json' }
		})
		.then(function (response) {
			if (response.data.hasOwnProperty('error')) {
				showDialogNotice('Error', response.data.message);
			} else {
				pref = response.data[0];
				pref.vrf = null;
				pref.pool = null;

				// Tags needs to be mangled for use with tags-input
				// TODO: When all interaction with prefix add & edit functions
				// are moved to AngularJS, change XHR functions to use the same
				// format as tags-input
				pref.tags = Object.keys(pref.tags).map(function (elem) { return { 'text': elem }; } );
				pref.inherited_tags = Object.keys(pref.inherited_tags).map(function (elem) { return { 'text': elem }; } );

				pref.avps = Object.keys(pref.avps).sort().map(function (key) { return { 'attribute': key, 'value': pref.avps[key] }; } );

				$scope.prefix = pref;

				// Fetch prefix's VRF
				$http.post('/xhr/smart_search_vrf',
					JSON.stringify({
						'vrf_id': $scope.prefix.vrf_id,
						'query_string': ''
					}),
					{ 'headers': { 'Content-Type': 'application/json' } })
					.then(function (response) {
						if (response.data.hasOwnProperty('error')) {
							showDialogNotice('Error', response.data.message);
						} else {
							$scope.prefix.vrf = response.data.result[0];
						}
					})
					.catch(function (response) {
						var msg = response.data || "Unknown failure";
						showDialogNotice('Error', response.status + ': ' + msg);
					});

				// Fetch prefix's pool, if any
				if ($scope.prefix.pool_id !== null) {
					$http.post('/xhr/list_pool',
						JSON.stringify({ 'id': $scope.prefix.pool_id }),
						{ 'headers': { 'Content-Type': 'application/json' } })
						.then(function (response) {
							if (response.data.hasOwnProperty('error')) {
								showDialogNotice('Error', response.data.message);
							} else {
								$scope.prefix.pool = response.data[0];
							}
						})
						.catch(function (response) {
							var msg = response.data || "Unknown failure";
							showDialogNotice('Error', response.status + ': ' + msg);
						});
				}

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
		.catch(function (response) {
			var msg = response.data || "Unknown failure";
			showDialogNotice('Error', response.status + ': ' + msg);
		});

	/*
	 * Form submitted
	 */
	$scope.submitForm = function () {

		// If prefix is owned by other system, ask user to verify the changes
		if ($scope.prefix.authoritative_source != 'nipap') {
			// TODO: Replace with AngularJS-style widget
			showDialogYesNo(
				'Confirm prefix edit',
				'The prefix ' + $scope.prefix.prefix + ' is managed by ' +
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
		delete prefix_data.vrf;

		// Mangle tags
		prefix_data.tags = $scope.prefix.tags.map(function (elem) { return elem.text; });
		// Mangle avps
		prefix_data.avps = {};
		$scope.prefix.avps.forEach(function(avp) {
			if (avp.attribute != '' && avp.value != '') {
				prefix_data.avps[avp.attribute] = avp.value;
			}
		});

		// handle null or 'infinity' as.. infinity
		if ($scope.prefix.expires == null) {
			// empty string signifies infinity
			prefix_data.expires = '';
		} else {
			// mangle date into ISO8601 format
			prefix_data.expires = $filter('date')($scope.prefix.expires, 'yyyy-MM-dd HH:mm:ss');
		}

		// Rewrite empty VLAN to null
		prefix_data.vlan = inputValidationHelpers.emptyToNull($scope.prefix.vlan);

		// Set pool, if any
		if ($scope.prefix.pool !== null) {
			prefix_data.pool = $scope.prefix.pool.id;
		}

		// Send query!
		$http.post('/xhr/edit_prefix/' + $scope.prefix.id,
				JSON.stringify(prefix_data),
				{ 'headers': { 'Content-Type': 'application/json' } })
			.then(function (response){
				if (response.data.hasOwnProperty('error')) {
					showDialogNotice('Error', response.data.message);
				} else {
					$scope.edited_prefixes.push(response.data);
				}
			})
			.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
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
		query_data.tags = $scope.vrf.tags.map(function (elem) { return elem.text; });
		query_data.avps = {};
		$scope.vrf.avps.forEach(function(avp) {
			if (avp.attribute != '' && avp.value != '') {
				query_data.avps[avp.attribute] = avp.value;
			}
		});

		// Send query!
		$http.post('/xhr/add_vrf',
				JSON.stringify(query_data),
				{ 'headers': { 'Content-Type': 'application/json' } })
			.then(function (response){
				if (response.data.hasOwnProperty('error')) {
					showDialogNotice('Error', response.data.message);
				} else {
					$scope.added_vrfs.push(response.data);
				}
			})
			.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
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
	$http.post('/xhr/smart_search_vrf',
		JSON.stringify({
			'vrf_id': $routeParams.vrf_id,
			'query_string': ''
			}),
			{ 'headers': { 'Content-Type': 'application/json' } })
		.then(function (response) {
			if (response.data.hasOwnProperty('error')) {
				showDialogNotice('Error', response.data.message);
			} else {
				vrf = response.data.result[0];

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
		.catch(function (response) {
			var msg = response.data || "Unknown failure";
			showDialogNotice('Error', response.status + ': ' + msg);
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
		query_data.tags = $scope.vrf.tags.map(function (elem) { return elem.text; });
		query_data.avps = {};
		$scope.vrf.avps.forEach(function(avp) {
			if (avp.attribute != '' && avp.value != '') {
				query_data.avps[avp.attribute] = avp.value;
			}
		});
		query_data.avps = query_data.avps;

		// Send query!
		$http.post('/xhr/edit_vrf/' + $scope.vrf.id,
				JSON.stringify(query_data),
				{ 'headers': { 'Content-Type': 'application/json' } })
			.then(function (response){
				if (response.data.hasOwnProperty('error')) {
					showDialogNotice('Error', response.data.message);
				} else {
					$scope.edited_vrfs.push(response.data);
				}
			})
			.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
			});

	}

});

/*
 * PoolAddController - used to add pools
 */
nipapAppControllers.controller('PoolAddController', function ($scope, $http, inputValidationHelpers) {

	$scope.method = 'add';
	$scope.added_pools = [];
	$scope.pool = {
		'name': null,
		'description': null,
		'tags': [],
		'default_type': null,
		'ipv4_default_prefix_length': null,
		'ipv6_default_prefix_length': null,
		'avps': []
	};

	// add another empty "extra attribute" (AVP) input row
	$scope.addAvp = function() {
		$scope.pool.avps.push({ 'attribute': '', 'value': '' });
	}

	// remove AVP row
	$scope.removeAvp = function(avp) {
		var index = $scope.pool.avps.indexOf(avp);
		$scope.pool.avps.splice( index, 1 );
	}

	/*
	 * Submit pool form - add pool
	 */
	$scope.submitForm = function() {

		/*
		 * Create object specifying pool attributes. Start with a copy of the
		 * pool object from the scope.
		 */
		var query_data = angular.copy($scope.pool);

		// Rewrite tags list to match what's expected by the XHR functions
		query_data.tags = $scope.pool.tags.map(function (elem) { return elem.text; });

		// Mangle avps
		query_data.avps = {};
		$scope.pool.avps.forEach(function(avp) {
			if (avp.attribute != '' && avp.value != '') {
				query_data.avps[avp.attribute] = avp.value;
			}
		});

		// Rewrite empty integers to null
		query_data.ipv4_default_prefix_length = inputValidationHelpers.emptyToNull($scope.pool.ipv4_default_prefix_length);
		query_data.ipv6_default_prefix_length = inputValidationHelpers.emptyToNull($scope.pool.ipv6_default_prefix_length);

		// Send query!
		$http.post('/xhr/add_pool',
				JSON.stringify(query_data),
				{ 'headers': { 'Content-Type': 'application/json' } })
			.then(function (response){
				if (response.data.hasOwnProperty('error')) {
					showDialogNotice('Error', response.data.message);
				} else {
					$scope.added_pools.push(response.data);
				}
			})
			.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
			});

	}

});

/*
 * PoolEditController - used to edit pools
 */
nipapAppControllers.controller('PoolEditController', function ($scope, $routeParams, $http, $uibModal, inputValidationHelpers) {

	$scope.method = 'edit';
	$scope.edited_pools = [];

	$scope.pool = {
		'tags': []
	};
	$scope.pool_prefixes = [];

	// add another empty "extra attribute" (AVP) input row
	$scope.addAvp = function() {
		$scope.pool.avps.push({ 'attribute': '', 'value': '' });
	}

	// remove AVP row
	$scope.removeAvp = function(avp) {
		var index = $scope.pool.avps.indexOf(avp);
		$scope.pool.avps.splice( index, 1 );
	}

	// Fetch pool to edit from backend
	$http.post('/xhr/list_pool',
		JSON.stringify({ 'id': $routeParams.pool_id }),
		{ 'headers': { 'Content-Type': 'application/json' } })
		.then(function (response) {
			if (response.data.hasOwnProperty('error')) {
				showDialogNotice('Error', response.data.message);
			} else {
				pool = response.data[0];

				// Tags needs to be mangled for use with tags-input
				// TODO: When all interaction with prefix add & edit functions
				// are moved to AngularJS, change XHR functions to use the same
				// format as tags-input
				pool.tags = Object.keys(pool.tags).map(function (elem) { return { 'text': elem }; } );

				pool.avps = Object.keys(pool.avps).sort().map(function (key) { return { 'attribute': key, 'value': pool.avps[key] }; } );

				// Fetch pool's VRF
				if (pool.vrf_id !== null) {
					$http.post('/xhr/smart_search_vrf',
						JSON.stringify({
							'vrf_id': $scope.pool.vrf_id,
							'query_string': ''
						}),
						{ 'headers': { 'Content-Type': 'application/json' } })
						.then(function (response) {
							if (response.data.hasOwnProperty('error')) {
								showDialogNotice('Error', response.data.message);
							} else {
								$scope.pool.vrf = response.data.result[0];
							}
						})
						.catch(function (response) {
							var msg = response.data || "Unknown failure";
							showDialogNotice('Error', response.status + ': ' + msg);
						});
				} else {
					pool.vrf = null;
				}

				$scope.pool = pool;

				// Fetch pool's prefixes
				$http.post('/xhr/list_prefix',
					JSON.stringify({ 'pool': pool.id }),
					{ 'headers': { 'Content-Type': 'application/json' } })
					.then(function (response) {
						if (response.data.hasOwnProperty('error')) {
							showDialogNotice('Error', response.data.message);
						} else {
							$scope.pool_prefixes = response.data;
						}
					})
					.catch(function (response) {
						var msg = response.data || "Unknown failure";
						showDialogNotice('Error', response.status + ': ' + msg);
					});

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

				var options = { animationSteps : 20, animationEasing: "easeOutQuart" };

				if (pool.member_prefixes_v4 > 0 && pool.ipv4_default_prefix_length !== null > 0) {
					var data_pool_prefixes_v4 = angular.copy(data_charts);
					data_pool_prefixes_v4[0]['value'] = pool.used_prefixes_v4;
					data_pool_prefixes_v4[1]['value'] = pool.free_prefixes_v4;

					var chart_pool_prefixes_v4 = new Chart($("#canvas_pool_prefixes_v4")[0]
						.getContext("2d"))
						.Doughnut(data_pool_prefixes_v4, options);
				}

				if (pool.member_prefixes_v6 > 0 && pool.ipv6_default_prefix_length !== null) {
					var data_pool_prefixes_v6 = angular.copy(data_charts);
					data_pool_prefixes_v6[0]['value'] = pool.used_prefixes_v6;
					data_pool_prefixes_v6[1]['value'] = pool.free_prefixes_v6;

					var chart_pool_prefixes_v6 = new Chart($("#canvas_pool_prefixes_v6")[0]
						.getContext("2d"))
						.Doughnut(data_pool_prefixes_v6, options);
				}

				if (pool.member_prefixes_v4 > 0) {
					var data_pool_addresses_v4 = angular.copy(data_charts);
					data_pool_addresses_v4[0]['value'] = pool.used_addresses_v4;
					data_pool_addresses_v4[1]['value'] = pool.free_addresses_v4;

					var chart_pool_addresses_v4 = new Chart($("#canvas_pool_addresses_v4")[0]
						.getContext("2d"))
						.Doughnut(data_pool_addresses_v4, options);
				}

				if (pool.member_prefixes_v6 > 0) {
					var data_pool_addresses_v6 = angular.copy(data_charts);
					data_pool_addresses_v6[0]['value'] = pool.used_addresses_v6;
					data_pool_addresses_v6[1]['value'] = pool.free_addresses_v6;

					var chart_pool_addresses_v6 = new Chart($("#canvas_pool_addresses_v6")[0]
						.getContext("2d"))
						.Doughnut(data_pool_addresses_v6, options);
				}

			}

		})
		.catch(function (response) {
			var msg = response.data || "Unknown failure";
			showDialogNotice('Error', response.status + ': ' + msg);
		});

	/*
	 * Submit pool form - edit pool
	 */
	$scope.submitForm = function () {

		/*
		 * Create object specifying pool attributes. Start with a copy of the
		 * pool object from the scope.
		 */
		var query_data = angular.copy($scope.pool);

		// Rewrite tags list to match what's expected by the XHR functions
		query_data.tags = $scope.pool.tags.map(function (elem) { return elem.text; });

		// Mangle avps
		query_data.avps = {};
		$scope.pool.avps.forEach(function(avp) {
			if (avp.attribute != '' && avp.value != '') {
				query_data.avps[avp.attribute] = avp.value;
			}
		});

		// Rewrite empty integer to null
		query_data.ipv4_default_prefix_length = inputValidationHelpers.emptyToNull($scope.pool.ipv4_default_prefix_length);
		query_data.ipv6_default_prefix_length = inputValidationHelpers.emptyToNull($scope.pool.ipv6_default_prefix_length);

		// Send query!
		$http.post('/xhr/edit_pool/' + $scope.pool.id,
				JSON.stringify(query_data),
				{ 'headers': { 'Content-Type': 'application/json' } })
			.then(function (response) {
				if (response.data.hasOwnProperty('error')) {
					showDialogNotice('Error', response.data.message);
				} else {
					$scope.edited_pools.push(response.data);
				}
			})
			.catch(function (response) {
					var msg = response.data || "Unknown failure";
					showDialogNotice('Error', response.status + ': ' + msg);
			});

	}

	/*
	 * Confirm remove of prefix from pool
	 */
	$scope.prefixConfirmRemove = function (evt, prefix) {

		var dialog = showDialogYesNo('Remove ' + prefix.display_prefix + '?',
			'Are you sure you want to remove ' + prefix.display_prefix + ' from pool? You cannot undo this action.',
			function () {

				$http.post('/xhr/edit_prefix/' + prefix.id,
						JSON.stringify({ 'pool': null }),
						{ 'headers': { 'Content-Type': 'application/json' } })
					.then(function (response) {
						if (response.data.hasOwnProperty('error')) {
							showDialogNotice('Error', response.data.message);
						} else {
							var index = $scope.pool_prefixes.indexOf(prefix);
							$scope.pool_prefixes.splice(index, 1);
						}
					})
					.catch(function (response) {
						var msg = response.data || "Unknown failure";
						showDialogNotice('Error', response.status + ': ' + msg);
					});

				dialog.dialog('close');

			}
		);

	}

	/*
	 * Display a popup notice informing the user of how pools are expanded
	 * nowadays.
	 */
	$scope.showExpandPoolNotice = function () {

		var modalInstance = $uibModal.open({
			templateUrl: 'expand_pool_notice.html',
			windowClass: 'nipap_modal'
		});

	}

});
