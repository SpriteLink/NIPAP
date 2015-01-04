/*
 * Services for the NIPAP AngularJS app
 */

var nipapAppServices = angular.module('nipapApp.services', []);

/*
 * Service with handy prefix helper functions
 */
nipapAppServices.factory('prefixHelpers', function () {

	var serviceInstance = {};

	/*
	 * Determines whether a prefix has maximum prefix length,
	 * /32 for IPv4 and /128 for IPv6.
	 */
	serviceInstance.maxPreflen = function(prefix) {

		// Check if 'prefix' is a host prefix or not,
		// see http://jsfiddle.net/AJEzQ/
		return /^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/32)?$|^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|:)))(\/128)?$/.test(prefix);

	}

	return serviceInstance;

});

