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
	 * Determines whether a prefix given as a string has maximum prefix length,
	 * /32 for IPv4 and /128 for IPv6.
	 */
	serviceInstance.maxPrefixLength = function(prefix) {

		// Check if 'prefix' is a host prefix or not,
		// see http://jsfiddle.net/AJEzQ/
		return /^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/32)?$|^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|:)))(\/128)?$/.test(prefix);

	}


	/*
	 * Determines whether a prefix described from metadata (family and length)
	 * has maximum prefix length.
	 */
	serviceInstance.maxPrefixLengthMeta = function(prefix_family, prefix_length) {

		return (prefix_family == 4 && parseInt(prefix_length) == 32) ||
			(prefix_family == 6 && parseInt(prefix_length) == 128);

	}

	/*
	 * Function which determines whether the Node input element should be enabled
	 * or not. It is only available when the prefix in question is configured as a
	 * node, ie the prefix is a /32 or /128.
	 *
	 * It's called from the prefix add and prefix edit page and as these pages look
	 * somewhat different we need to account for some stuff.
	 */
	serviceInstance.enableNodeInput = function(prefix, alloc_method, prefix_type, prefix_length, prefix_family) {

		/*
		 * Generally, the node option should only be available for host prefixes.
		 * However, there is one exception: loopbacks, which are defined as
		 * assignments with max prefix length.
		 */

		 // See if prefix type is set
		 if (prefix_type == 'reservation') {

			// reservation - disable no matter what
			return false;

		 } else if (prefix_type == 'host') {

			// host - enable no matter what
			return true;

		 } else if (prefix_type == 'assignment') {

			/*
			 * Assignment - more tricky case!
			 *
			 * If we add a prefix from a pool or other prefix, we use prefix
			 * length and prefix family to determine if the prefix will have
			 * max prefix length.  If we add manually, we use a super-regex to
			 * determine if it is a host prefix directly from the prefix
			 * string.
			 */
			if (alloc_method == 'from-pool' || alloc_method == 'from-prefix') {

				return serviceInstance.maxPrefixLengthMeta(prefix_family, prefix_length);

			} else {

				return serviceInstance.maxPrefixLength(prefix);

			}

		 } else {

			// prefix type not set - disable
			return false;

		 }

	}

	return serviceInstance;

});


/*
 * Service with handy input validation and mangling functions
 */
nipapAppServices.factory('inputValidationHelpers', function () {

	var serviceInstance = {};

	/*
	 * Convert empty strings to null and strip whitespace
	 */
	serviceInstance.emptyToNull = function(value) {

		// Rewrite empty string to null
		if ($.trim(value) === '') {
			return null;
		} else {
			return $.trim(value);
		}

	};

	return serviceInstance;

});
