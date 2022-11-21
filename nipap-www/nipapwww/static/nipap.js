/**********************************************************************
 *
 * NIPAP JavaScript functions
 *
 *********************************************************************/

/*
 * Settings
 */
var PREFIX_BATCH_SIZE = 50;

/**
 * Global variables...
 */

/*
 * The prefix_list variable is used to keep a copy of all the prefixes
 * currently in the displayed list.
 */
var prefix_list = new Object();
var pool_list = new Object();
var indent_head = new Object();
var selected_vrfs = new Object();
var vrf_list = {
	'null': {
		'id': null,
		'rt': null,
		'name': null
	}
};

// Object for storing statistics
var stats = new Object();

// current options - mostly used for prefix addition on
// the prefix add and pool edit pages.
var cur_opts = new Object();

/*
 * Holy shit, this is an ugly hack...
 * As the prefix search results sometimes need to link to an edit-prefix-page
 * and sometimes need to link to a select-prefix function, we keep the current
 * state in a global variable...
 */
var prefix_link_type = 'edit';
var current_page = null;

// Max prefix lengths for different address families
var max_prefix_length = [32, 128];

var current_query = {
	'query_string': '',
	'parents_depth': 0,
	'children_depth': 0
};
var query_id = 0;
var newest_prefix_query = 0;
var newest_vrf_query = 0;

// place to store current VRF selector callback function
var curVRFCallback = null;

var offset = 0;
var outstanding_nextpage = 0;
var end_of_result = 1;
var explicit = false;

var search_key_timeout = 0;

// store current container for inserting prefixes
var container = null;

// Keep track of whether we arrived at a 'popped state' or
// ordinary page load
var popped = null;
var initialURL = null;

// Translate operators to text strings
var operator_map = {
	'=': 'equal',
	'!=': 'not equal',
	'>': 'greater than',
	'>=': 'greater than or equal',
	'<': 'smaller than than',
	'<=': 'smaller than or equal',
	'~': 'a regular expression match'
};

/**
 * A general log function
 *
 * This will try to post a message to the javascript console available in
 * Chrome / Firefox, if that's not available, it'll try opera and thereafter
 * give up.
 */
function log(msg) {
	try {
		console.log(msg);
	} catch (error) {
		try {
			window.opera.postError(msg)
		} catch (error) {
			// no console available
		}
	}
}

/**
 * Display a notice popup
 *
 * @param title string Title to display above error message.
 * @param msg Message to display to user.
 */
function showDialogNotice(title, msg) {

	var dialog = $('<div>' + msg + '</div>')
		.dialog({
			autoOpen: false,
			resizable: false,
			show: 'fade',
			hide: 'fade',
			open: function() {
				$('.ui-widget-overlay').hide().fadeIn('fast');
				$(this).parents(".ui-dialog:first").find(".ui-dialog-titlebar").addClass("ui-dialog-question");
				$(this).parents(".ui-dialog:first").find(".ui-dialog-titlebar-close").remove();
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-button");
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-widget");
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-corner-all");
				$(this).parents(".ui-dialog:first").find(":button:eq(0)").addClass("btn btn-success");
			},
			modal: true,
			title: title,
			buttons: [
				{
					style: 'margin: 10px; width: 50px;',
					text: "OK",
					click: function() { $(this).dialog("close"); }
				}
			]
		});

	dialog.dialog('open');

	return false;
}

/*
 * Show general confirm dialog
 */
function showDialogYesNo(title, msg, target_yes) {
	var dialog = $('<div>' + msg + '</div>')
		.dialog({
			autoOpen: false,
			resizable: false,
			show: 'fade',
			hide: 'fade',
            width: 400,
			open: function() {
				$('.ui-widget-overlay').hide().fadeIn('fast');
				$(this).parents(".ui-dialog:first").find(".ui-dialog-titlebar").addClass("ui-dialog-question");
				$(this).parents(".ui-dialog:first").find(".ui-dialog-titlebar-close").remove();
				// XXX: this is a bloody hack to override the jquery ui CSS
				//		classes, or rather remove them and have our standard
				//		button look instead
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-button");
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-widget");
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-corner-all");
				$(this).parents(".ui-dialog:first").find(":button:eq(0)").addClass("btn btn-danger");
				$(this).parents(".ui-dialog:first").find(":button:eq(1)").addClass("btn btn-success");
			},
			modal: true,
			title: title,
			buttons: [
				{
					style: 'margin: 10px; width: 50px;',
					text: "Yes",
					click: target_yes
				},
				{
					style: 'margin: 10px; width: 50px;',
					text: "No",
					click: function() { $(this).dialog("close"); }
				}
			]
		});

	dialog.dialog('open');

	return dialog;
}


/*
 * Show general dialog
 */
function showDialog(id, title, content, width) {
	// figure out default width
	if (width == undefined) {
		width = 400;
	} else {
		width = parseInt(width);
	}

	var c = '<div>' + content + '</div>';

	var dialog = $(c)
		.dialog({
			autoOpen: false,
			resizable: false,
			show: 'fade',
			hide: 'fade',
			open: function() {
				$('.ui-widget-overlay').hide().fadeIn('fast');
			},
			modal: true,
			width: width,
			title: title
		});

	dialog.dialog('open');

	return dialog;
}


/*
 * Display the search help "pop-up".
 */
function displaySearchHelp() {

	var c = '';

	c += '<div class="dialog_text" style="padding: 15px;">' +
		"Searching is the primary method of navigating the many thousand of prefixes that NIPAP is built to handle. It's very similar to how popular search engines, such as Google, Yahoo or Bing, are used." +
		"<h4>Matching text</h4>Just as with any search engine, you can enter a word or multiple words to match the text information associated with a prefix, that is the description or comment field. Each word is treated as a search 'term' and all search terms are joined together by the boolean operator AND. That means that searching for <i>'<b>foo bar</b>'</i> will be interpreted as a search for <i>'<b>foo</b>'</i> and <i>'<b>bar</b>'</i>. Any match must contain both the word <i>'<b>foo</b>'</i> and the word <i>'<b>bar</b>'</i>, though not necessarily in that order. <i>'<b>bar foo</b>'</i> will match, just as <i>'<b>foo</b> test test <b>bar</b>'</i> will match." +
		   "<h4>IP addresses / prefixes</h4>Searching for IP addresses are specially treated and will only match in the IP address column. Simply enter a complete IPv4 or IPv6 address and it will be automatically interpreted as an IP address.<br/><br/>It is possible to match entire prefixes and all their content by searching for a prefix in CIDR notation (e.g. 192.168.1.0/24). Searching for 192.168.1.x or 192.168.1 (as some would expect to match everything in 192.168.1.0/24) will not work as they will not be interpreted as prefixes but as text." +
		   "<h4>VRF selector</h4>The VRF selector is located in the top left corner and is used to filter the prefix search to prefixes within the listed VRFs. Press the + to add one or more VRFs to the VRF list. Prefix search results will only include prefixes that are within the VRFs in the list. If no VRFs are specified with the VRF selector the prefix search will list prefixes from all VRFs. " +
		   "<h4>Matching tags</h4>To search for a prefix with a certain tag, simply type '#foo', where 'foo' is the name of the tag. The search will match any prefix that has this tag set or that 'inherits' it from an encompassing prefix. Only exact matches are given and it is not possible to use regexp or similar to match tags." +
		   "<h3>Examples</h3>" +
		   "To find what the IP address 192.168.1.1 is used for:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;192.168.1.1" +
		   "<br/><br/>To list all addresses inside 172.16.0.0/24:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;172.16.0.0/24" +
		   "<br/><br/>To match prefixes with 'TEST-ROUTER-1' in description or comment and that are somewhere in the network 10.0.0.0/8:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;10.0.0.0/8 TEST-ROUTER-1" +
		   "<br/><br/>To match prefixes with tag 'core' and description or comment 'router':<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;#core router" +
		   '<br/><br/></div>';
	d = showDialog('search_help', 'Searching', c, 800);

	return false;
}



/*
 * Display "pop-up" with help about the prefix types.
 */
function displayPrefixTypeHelp() {

	var c = '';
	c += '<div class="dialog_text" style="padding: 15px;">' +
		"Prefix types is an artificial construct to ensure consistency in the NIPAP data. Each prefix must have a type, either 'reservation', 'assignment' or 'host'.<br/><br/>" +
		"'host' are used to document individual hosts in a subnet, while 'assignments' are used to document prefixes with a \"specific use\", a \"subnet\". For example, a /30 link network is an 'assignment' while the two individual usable addresses inside the /30 are 'hosts'.<br/><br/>" +
		"'reservation' differs from 'assignment' in that a reservation is not yet meant for a specific use, ie it is not used in the network. If you want to reserve a larger prefix for use a link networks, you would create a 'reservation', perhaps a /24. Within that network you could then assign /30s or /31s into 'assignments' and in them document the individual hosts. The /24 'reservation' is only reserved for link networks.<br/><br/>" +
		"As a rule of thumb, you will likely find 'assignments' in the routing table while most 'reservations' will not be in your routing table (except for large aggregates)." +
		   '<br/><br/></div>';

	d = showDialog('prefix_type_help', 'Prefix types', c, 800);

	return false;
}


/*
 * Error handler for ajax-errors.
 *
 * Function designed to be passed as error callback to i.e. getJSON().
 */
function ajaxErrorHandler(e, jqXHR, ajaxSettings, thrownError) {

	showDialogNotice('Server error', thrownError);

}


/**********************************************************************
 *
 * Prefix list functions
 *
 *********************************************************************/

/*
 * Expands a collapse group
 */
function expandGroup(id) {

	var col = $('#collapse' + id);
	var exp = $('#prefix_exp' + id);

	col.slideDown();
	exp.html('&ndash;');
}

/*
 * Collapse a collapse group
 */
function collapseGroup(id) {

	var col = $('#collapse' + id);
	var exp = $('#prefix_exp' + id);

	col.slideUp();
	exp.html('+');

}

/*
 * Clear all state related to prefix search
 */
function clearPrefixSearch() {
	$('#search_interpretation').empty();
	$('#search_stats').empty();
	$('#prefix_list').empty();
	$('#fixed_prefix_header').css('visibility', 'hidden');
	$('#nextpage').hide();
	query_id += 1;

	current_query = {
		'query_string': '',
		'parents_depth': 0,
		'children_depth': 0
	};

	end_of_result = 1;

}

/*
 * Wrapper for pacing our searches somewhat
 *
 * 500 ms works out to be a pretty good compromise
 */
function prefixSearchKey() {
	clearTimeout(search_key_timeout);
	search_key_timeout = setTimeout(function() { performPrefixSearch(false) }, 500);
}

/*
 * Perform a search operation
 *
 * The argument 'force_explicit' can be used to force an explicit search. The
 * new valye will ve stored in the global 'explicit' variable.
 *
 * By setting the argument 'popping_state' to true we're telling
 * performPrefixSearch that the search operation occurred due to a
 * popstate-event. This means that we should avoid updating
 * window.location.href and pushing a new state.
 */
function performPrefixSearch(force_explicit, update_uri) {

	if (force_explicit !== undefined && force_explicit !== null) {
		explicit = force_explicit;
	}

	var search_q = {
		'query_id': query_id,
		'query_string': $('#query_string').val(),
		'parents_depth': optToDepth($('input[name="search_opt_parent"]:checked').val()),
		'children_depth': optToDepth($('input[name="search_opt_child"]:checked').val()),
		'include_all_parents': 'true',
		'include_all_children': 'false',
		'include_neighbors': 'true',
		'max_result': PREFIX_BATCH_SIZE,
		'offset': 0,
		'vrf_filter': []
	}

	query_id += 1;

	// Find what VRFs has been added to VRF filter
	$.each(selected_vrfs, function(k, v) {
		search_q.vrf_filter.push(String(v.id));
	});

	// Skip search if it's equal to the currently displayed search
	if (
		(search_q.query_string == current_query.query_string &&
		 search_q.parents_depth == current_query.parents_depth &&
		 search_q.children_depth == current_query.children_depth)
		 && explicit == false) {
		return true;
	}

	// If query string is empty display top level prefixes
	if (jQuery.trim($('#query_string').val()).length < 1) {
		// indent = 0 makes sure we only get the top-level prefixes
		search_q.indent = 0;
		clearPrefixSearch();
	}

	end_of_result = 0;

	current_query = search_q;
	offset = 0;

	$('#prefix_list').empty();
	if (prefix_link_type == 'edit') {
		$('#fixed_prefix_header').css('visibility', 'visible');
	}

	showLoadingIndicator($('#prefix_list'));

	// Keep track of search timing
	stats.query_sent = new Date().getTime();

	$.ajax({
		type: "POST",
		url: "/xhr/smart_search_prefix",
		data: JSON.stringify(current_query),
		success: receivePrefixList,
		dataType: "json",
		contentType: "application/json"
	});

    // add search options to URL unless the search operation was performed due
    // to a popstate-event
    if (update_uri !== false) {
        setSearchPrefixURI();
    }

}


/*
 * Extract search options and add to URI
 */
function setSearchPrefixURI() {

	var url = $.url();
	var url_str = "";

	url_str = url.attr('protocol') + '://' + url.attr('host');

	if (url.attr('port') != null) {
		url_str += ":"+url.attr('port');
	}

	url_str += url.attr('path');

	if (url.attr('query') != null && url.attr('query') != '') {
		url_str += '?' + url.attr('query');
	}

	url_str += '#/query_string=' +
		encodeURIComponent($('#query_string').val()) +
		'&search_opt_parent=' +
		encodeURIComponent($('input[name="search_opt_parent"]:checked').val()) +
		'&search_opt_child=' +
		encodeURIComponent($('input[name="search_opt_child"]:checked').val()) +
		'&explicit=' + encodeURIComponent(explicit);

	history.pushState(true, null, url_str);

}


/*
 * Called when next page of results is requested by the user.
 */
function performPrefixNextPage() {

	// Skip nextpage if we're already performing one or we've reached the end
	// of the result.
	if (outstanding_nextpage == 1 || end_of_result == 1) {
		return;
	}

	outstanding_nextpage = 1;

	offset += PREFIX_BATCH_SIZE - 1;

	current_query.query_id = query_id;
	current_query.offset = offset;

	query_id += 1;

	showLoadingIndicator($('#prefix_list'));

	// Keep track of search timing
	stats.query_sent = new Date().getTime();

	$.ajax({
		type: "POST",
		url: "/xhr/smart_search_prefix",
		data: JSON.stringify(current_query),
		success: receivePrefixListNextPage,
		dataType: "json",
		contentType: "application/json"
	});

}


/*
 * Add a prefix to the prefix list.
 *
 * A prefix can be placed in two ways, either in a container or relative to
 * another prefix. If a container is given, the prefix is simply added to it. If
 * relative placement is asked for, the prefix can instead be placed before or
 * after an already existing prefix.
 *
 * Use the options 'relative' and 'offset' to determine where to place the
 * prefix. 'reference' should be an object which will be used as reference for
 * the placement and 'offset' determines where how to offset the new object
 * relative to 'reference'.
 *
 * 'offset' can take the following values:
 * append - append element into reference
 * prepend - prepend element into reference
 * before - place element before reference
 * after - place element after reference
 */
function showPrefix(prefix, reference, offset) {

	// add main prefix container
	var econt = '<div id="prefix_entry' + prefix.id + '" data-prefix-id="' + prefix.id + '">';
	if (offset == null) {
		reference.append(econt);
	} else if (offset == 'before') {
		reference.before(econt);
	} else if (offset == 'after') {
		reference.after(econt);
	} else if (offset == 'prepend') {
		reference.prepend(econt);
	} else {
		log("Invalid offset " + offset);
	}

	var prefix_entry = $('#prefix_entry' + prefix.id);
	prefix_entry.data('prefix_id', prefix.id);
	prefix_entry.addClass('prefix_entry');
	prefix_entry.append('<div id="prefix_row' + prefix.id + '">');
	var prefix_row = $('#prefix_row' + prefix.id );
	if (prefix.match == true) {
		prefix_row.addClass("row_match");
	} else {
		prefix_row.addClass("row_collateral");
	}

	// add indent and prefix container
	prefix_row.append('<div id="prefix_ind_pref' + prefix.id + '">');
	var prefix_ind_pref = $('#prefix_ind_pref' + prefix.id);
	prefix_ind_pref.addClass('prefix_column');
	prefix_ind_pref.addClass('prefix_ind_pref');

	// add indent
	prefix_ind_pref.append('<div id="prefix_indent' + prefix.id + '">');
	var prefix_indent = $('#prefix_indent' + prefix.id);
	prefix_indent.addClass("prefix_indent");
	prefix_indent.html('<div id="prefix_exp' + prefix.id + '"></div>');
	var prefix_exp = $('#prefix_exp' + prefix.id);
	prefix_exp.addClass("prefix_exp");

	// If the prefixes has children (or we do not know), add expand button
	if (prefix.children == 0) {

		// the prefix_indent container must contain _something_
		prefix_exp.html('&nbsp;');

	} else {

		// add expand button
		prefix_exp.html('+');
		$('#prefix_exp' + prefix.id).click(function (e) {
			collapseClick(prefix.id);
			e.stopPropagation();
		});

	}

	prefix_indent.width(prefix_indent.width() + 15 * prefix.indent);

	// add prefix
	prefix_ind_pref.append('<div id="prefix_prefix' + prefix.id + '">');
	var prefix_prefix = $('#prefix_prefix' + prefix.id);
	prefix_prefix.addClass('prefix_column');
	prefix_prefix.addClass('prefix_prefix');

	// Different actions for different list types...
	// First: select a prefix in the list
	if (prefix_link_type == 'select') {

		prefix_prefix.html('<a href="javascript:void(0);" onClick="selectPrefix(' +
			prefix.id + '); return false;">' + prefix.display_prefix + '</a>');

	// Add prefix to pool
	} else if (prefix_link_type == 'add_to_pool') {

		prefix_prefix.html('<a href="/pool/add_prefix/' + pool_id + '?prefix=' +
			prefix.id + '" onClick="addToPool(' + prefix.id +
			'); return false;">' + prefix.display_prefix + '</a>');

	// Or edit prefix
	} else {
		prefix_prefix.html(prefix.display_prefix);
	}

	// add button if list not used to select prefix to add to pool or select
	// prefix to allocate from
	if (prefix_link_type != 'select' && prefix_link_type != 'add_to_pool') {
		prefix_row.append('<div id="prefix_button_col' + prefix.id + '">');
		var prefix_button_col = $('#prefix_button_col' + prefix.id);
		prefix_button_col.addClass('prefix_column');
		prefix_button_col.addClass('prefix_button_col');
		prefix_button_col.append('<div id="prefix_button' + prefix.id + '" data-prefix-id="' + prefix.id + '">');

		var prefix_button = $('#prefix_button' + prefix.id);
		prefix_button.addClass('minibutton');
		prefix_button.html('<div class="popup_button_icon">&nbsp;</div>');
		prefix_button.click(prefix, function(e) {
			showPrefixMenu(e.currentTarget.getAttribute('data-prefix-id'));
			e.preventDefault();
			e.stopPropagation();
		});
	}

	// Add prefix type
	prefix_row.append('<div id="prefix_type' + prefix.id + '">');
	var prefix_type = $('#prefix_type' + prefix.id);
	prefix_type.addClass('prefix_column');
	prefix_type.addClass('prefix_type');
	prefix_type.append('<div id="prefix_type_icon' + prefix.id + '">');
	var prefix_type_icon = $('#prefix_type_icon' + prefix.id);
	prefix_type_icon.addClass('prefix_type_icon');
	prefix_type_icon.addClass('prefix_type_' + prefix.type);

	// Add tooltip to prefix type icon
	prefix_type_icon.attr('uib-tooltip', prefix.type[0].toUpperCase() + prefix.type.slice(1));
	prefix_type_icon.html(prefix.type[0].toUpperCase());
	// Run element through AngularJS compiler to "activate" directives (the
	// AngularUI/Bootstrap tooltip)
	prefix_type_icon.replaceWith(ng_compile(prefix_type_icon)(ng_scope));
	ng_scope.$apply();

	// Add tags
	prefix_row.append('<div id="prefix_tags' + prefix.id + '">');
	var prefix_tags = $('#prefix_tags' + prefix.id);
	prefix_tags.addClass('prefix_column');
	prefix_tags.addClass('prefix_tags');
	if ((prefix.tags == null || $.isEmptyObject(prefix.tags)) && (prefix.inherited_tags == null || $.isEmptyObject(prefix.inherited_tags))) {
		prefix_tags.html("&nbsp;");
	} else {
		sort_func = function(a, b) { return a.toLowerCase().localeCompare(b.toLowerCase()); }

		var tag_list = Object.keys(prefix.tags).sort(sort_func).join('<br/>');
		if (prefix.tags.length == 1 ) {
			tag_list += '<br/>'
		}

		tags_html = '"<div style=\\"text-align: left;\\">Tags:<br/>' +
			tag_list +
			'<br>Inherited tags:<br/>' +
			Object.keys(prefix.inherited_tags).sort(sort_func).join('<br/>') +
			'</div>"';

		prefix_tags.html('<img src="/images/tag-16.png">');
		prefix_tags.children().attr('uib-tooltip-html', tags_html);
		// Run element through AngularJS compiler to "activate" directives (the
		// AngularUI/Bootstrap tooltip)
		prefix_tags.replaceWith(ng_compile(prefix_tags)(ng_scope));
		ng_scope.$apply();
	}


	// Add node
	prefix_row.append('<div id="prefix_node' + prefix.id + '">');
	var prefix_node = $('#prefix_node' + prefix.id);
	prefix_node.addClass('prefix_column');
	prefix_node.addClass('prefix_node');
	if (prefix.node == null || prefix.node == '') {
		prefix_node.html("&nbsp;");
	} else {
		prefix_node.html(prefix.node);
	}

	// Add order number
	prefix_row.append('<div id="prefix_order_id' + prefix.id + '">');
	var prefix_order_id = $('#prefix_order_id' + prefix.id);
	prefix_order_id.addClass('prefix_column');
	prefix_order_id.addClass('prefix_order_id');
	if (prefix.order_id == null || prefix.order_id == '') {
		prefix_order_id.html("&nbsp;");
	} else {
		prefix_order_id.html(prefix.order_id);
	}

    // Add Customer ID
	prefix_row.append('<div id="prefix_customer_id' + prefix.id + '">');
	var prefix_customer_id = $('#prefix_customer_id' + prefix.id);
	prefix_customer_id.addClass('prefix_column');
	prefix_customer_id.addClass('prefix_customer_id');
	if (prefix.customer_id == null || prefix.customer_id == '') {
		prefix_customer_id.html("&nbsp;");
	} else {
		prefix_customer_id.html(prefix.customer_id);
	}

    // Add comment icon if a comment is present
	prefix_row.append('<div id="prefix_comment' + prefix.id + '">');
	var prefix_comment = $('#prefix_comment' + prefix.id);
	prefix_comment.addClass('prefix_column');
	prefix_comment.addClass('prefix_comment');
	if (prefix.comment == null || prefix.comment == '') {
		prefix_comment.html("&nbsp;");
	} else {
		prefix_comment.html('<img src="/images/comments-16.png">');
		prefix_comment.children().attr('uib-tooltip', prefix.comment);
		prefix_comment.replaceWith(ng_compile(prefix_comment)(ng_scope));
		ng_scope.$apply();
	}

	// Add prefix description
	prefix_row.append('<div id="prefix_description' + prefix.id + '">');
	var prefix_description = $('#prefix_description' + prefix.id);
	prefix_description.addClass('prefix_column');
	prefix_description.addClass('prefix_description');
	if (prefix.description == null || prefix.description == '') {
		prefix_description.html("&nbsp;");
	} else {
		prefix_description.html(prefix.description);
	}

	// add collapse container
	if (!hasMaxPreflen(prefix)) {
		prefix_entry.after('<div class="prefix_collapse" id="collapse' + prefix.id + '">');
	}

}

/*
 * Function which is run when a prefix has been removed
 */
function prefixRemoved(prefix) {

	if ('error' in prefix) {
		showDialogNotice("Error", prefix.message);
		return;
	}

	// remove prefix from list
	$('#prefix_entry' + prefix.id).remove();
	$('#collapse' + prefix.id).remove();

}


/*
 * Build a popup menu
 */
function getPopupMenu(ref, title, data_id) {

	// Add popup menu
	var name = 'popupmenu_' + data_id;
	$('body').append('<div id="' + name + '">');
	var menu = $('#' + name);
	menu.addClass("popup_menu");
	menu.html("<h3>" + title + "</h3>");

	// show overlay
	$('body').append('<div class="popup_overlay"></div>');
	$(".popup_overlay").click(function() { hidePopupMenu() });
	$(".popup_overlay").show();

	// Set menu position
	menu.css('top', ref.offset().top + ref.height() + 5 + 'px');
	menu.css('left', ref.offset().left + 'px');

	return menu;

}

/*
 * Show the prefix menu
 */
function showPrefixMenu(prefix_id) {

	// Add prefix menu
	var button = $('#prefix_button' + prefix_id);
	var menu = getPopupMenu(button, 'Prefix', prefix_id);

	// Add different manu entries depending on where the prefix list is displayed
	if (prefix_link_type == 'select') {
		// select prefix (allocate from prefix function on add prefix page)
	} else if (prefix_link_type == 'add_to_pool') {
		// Add to pool (Add prefix to pool on edit pool page)
	} else {
		// ordinary prefix list
		menu.append('<a href="/ng/prefix#/prefix/edit/' + prefix_id + '">Edit</a>');
		menu.append('<a id="prefix_remove' + prefix_id + '" href="/prefix/remove/' + prefix_id + '">Remove</a>');

        // Create prefix remove dialog text and actions dependent on
        // authoritative source of prefix
        auth_src = prefix_list[prefix_id].authoritative_source;
        if (auth_src == 'nipap') {

            confirmation_text = 'Are you sure you want to remove the prefix ' +
                prefix_list[prefix_id].display_prefix + '?';

            confirmation_action = function() {
				$.getJSON('/xhr/remove_prefix/' + prefix_id, prefixRemoved);

				hidePopupMenu();
				$(this).dialog('close');

			}

        } else {

            confirmation_text = 'Prefix ' + prefix_list[prefix_id].prefix + ' is managed by \'' +
                auth_src + '\'.<br>' +
                'Are you sure you want to remove it?<br><br>' +
                'Enter the name of the managing system to continue:<br>' +
                '<input type="text" id="confirm_prefix_remove" style="width: 95%;">' +
                '<div id="auth_src_mismatch" style="display: none; color: red;">System names did not match.</div>';

            confirmation_action = function() {

                if ($('#confirm_prefix_remove').val().toLowerCase() == auth_src.toLowerCase()) {

                    // User entered correct auth scr, remove prefix
				    $.getJSON('/xhr/remove_prefix/' + prefix_id, prefixRemoved);

				    hidePopupMenu();
				    $(this).dialog('close');

                } else {

                    // Wrong auth src entered
                    $('#auth_src_mismatch').fadeIn();

                }
            }
        }

		$('#prefix_remove' + prefix_id).click(function(e) {
			e.preventDefault();
			hidePopupMenu();
			var dialog = showDialogYesNo('Really remove prefix?', confirmation_text, confirmation_action);
        });

		// Add button to add prefix from prefix, unless it's of max prefix length
		if (!hasMaxPreflen(prefix_list[prefix_id])) {
			menu.append('<a href="/ng/prefix#/prefix/add/from-prefix/' + prefix_id + '">Add prefix from prefix</a>');
		}

	}

	menu.slideDown('fast');

}

/*
 * Show VRF selector menu
 *
 * The function passed in parameter 'callback' will be called as
 * callback(vrf_list) when the user has finished selecting VRFs.
 */
function showVRFSelectorMenu(callback, pl_ref) {

	// As we can not pass the callback all the way until the result from
	// getJSON query is received, we store it in a global variable
	curVRFCallback = callback;

	// Create a generic popup menu and make it a selector
	menu = getPopupMenu(pl_ref, "Select VRF", '');
	menu.addClass('selector');

	// Add search filter
	menu.append('<div class="selector_filterbar"></div>');
	menu.children('.selector_filterbar').append('<input type="text" class="selector_search_string" name="vrf_search_string">');
	$('input[name="vrf_search_string"]').keyup(vrfSearchKey);

	menu.append('<div class="selector_result"></div>');

	// Set focus to text box, after all other processing is done
	setTimeout(function() { $('input[name="vrf_search_string"]').focus(); }, 0);

	menu.slideDown('fast');

	// and do a search to display the default VRF at least
	performVRFSelectorSearch();

}

/*
 * Wrapper for pacing our searches somewhat
 *
 * 500 ms works out to be a pretty good compromise
 *
 * TODO: merge with prefixSearchKey
 */
function vrfSearchKey() {
	clearTimeout(search_key_timeout);
	search_key_timeout = setTimeout("performVRFSelectorSearch()", 500);
}

/*
 * Perform VRF selector search operation
 */
function performVRFSelectorSearch() {

	// Keep track of search timing
	stats.vrf_query_sent = new Date().getTime();

	var search_q = {
		'query_id': query_id,
		'query_string': $('input[name="vrf_search_string"]').val(),
		'max_result': 10,
		'offset': 0
	}

	// Search for vrf id 0 on empty search as to display the default VRF if no
	// other search is performed
	if (jQuery.trim($('input[name="vrf_search_string"]').val()).length < 1) {
		search_q['vrf_id'] = 0;
	}

	query_id += 1;
	offset = 0;

	$('.selector_result').empty();
	showLoadingIndicator($('.selector_result'));
	$.ajax({
		type: "POST",
		url: "/xhr/smart_search_vrf",
		data: JSON.stringify(search_q),
		success: receiveVRFSelector,
		dataType: "json",
		contentType: "application/json"
	});

}

/*
 * Add single VRF to displayed list of selected vrfs
 */
function addVRFToSelectList(vrf, elem) {

	elem.append('<a href="#" id="vrf_filter_entry_' + String(vrf.id) + '" ' +
		'class="vrf_filter_entry" data-vrf_id="' + String(vrf.id) + '" data-vrf_rt="' + ( vrf.rt == null ? '-' : vrf.rt ) + 
		'" data-vrf_name="' + vrf.name + '" data-vrf_description="' + vrf.description + '">' +
			'<div><div class="selector_tick">&nbsp;</div><div class="vrf_filter_entry_rt">RT:&nbsp;' +
			( vrf.id == 0 ? '-' : vrf.rt ) + '</div>' + vrf.name + '</div>' +
			'<div class="selector_entry_description">' +
			( vrf.description == null ? '' : vrf.description ) + '</div><div class="selector_x">&nbsp;</div></a>');

	// display tick
	if (selected_vrfs.hasOwnProperty(String(vrf.id))) {
		elem.children('#vrf_filter_entry_' + String(vrf.id)).children().children('.selector_tick').html('&#10003;');
		elem.children('#vrf_filter_entry_' + String(vrf.id)).children('.selector_x').html('<img src="/images/x-mark-3-16.png">');
	}

	$("#vrf_filter_entry_" + String(vrf.id)).click(curVRFCallback);

}

/*
 * Receive VRF selector search result
 *
 * Receive search result and display in destined container.
 */
function receiveVRFSelector(result) {

	// Boilerplate... statistics, handle errors...
	stats.response_received = new Date().getTime();

	if (! ('query_id' in result.search_options)) {
		showDialogNotice("Error", 'No query_id');
		return;
	}
	if (parseInt(result.search_options.query_id) < parseInt(newest_vrf_query)) {
		return;
	}
	newest_vrf_query = parseInt(result.search_options.query_id);

	// Error?
	if ('error' in result) {
		showDialogNotice("Error", result.message);
		return;
	}

	// empty VRF container
	var vrf_cont = $('.selector_result');
	vrf_cont.empty();

	// If it's a search for the default VRF, ie empty search, then display the
	// currently selected VRFs. For other search, we don't show the currently
	// selected to avoid cluttering the result list.
	if ($('input[name="vrf_search_string"]').val() == "") {
		// add selected VRFs to the selectedbar
		$.each(selected_vrfs, function (k, v) {
			// except for the default VRF, since that will already be included
			// in the search result
			if (k != 0) {
				addVRFToSelectList(v, $('.selector_result'));
			}
		});
	}

	// place search result in VRF container
	if (result.result.length > 0) {
		for (i = 0; i < result.result.length; i++) {

			var vrf = result.result[i];

			// Add to global list of current VRFs
			vrf_list[vrf.id] = vrf;

			addVRFToSelectList(vrf, vrf_cont);
		}
	} else {
		vrf_cont.append('<div style="padding: 10px;">No VRF found</div>');
	}

}

/*
 * Run when a VRF is selected for a prefix
 */
function clickPrefixVRFSelector(evt) {

	var tgt = evt.target;
	while (true) {
		if (tgt.hasAttribute('data-vrf_id')) {
			break
		}
		tgt = tgt.parentElement;
	}
	var vrf = Object();
	vrf.id = tgt.getAttribute('data-vrf_id');
	vrf.rt = tgt.getAttribute('data-vrf_rt');
	vrf.name = tgt.getAttribute('data-vrf_name');
	vrf.description = tgt.getAttribute('data-vrf_description');
	$("#prefix_vrf_display").html('<div class="vrf_filter_entry"><div class="vrf_filter_entry_rt">RT:&nbsp;' + vrf.rt + '</div><div class="selector_entry_name" style="margin-left: 5px;">' + vrf.name + '</div><div class="selector_entry_description" style="clear: both;">' + vrf.description + '</div></div>');

	// update VRF input field with selected VRF
	$('input[name="prefix_vrf_id"]').val(vrf.id);
	$("#prefix_vrf_text").html('Manually selected VRF:');

	hidePopupMenu();
	evt.preventDefault();

}

/*
 * Run when a VRF is selected for filtering in the VRF selector
 */
function clickFilterVRFSelector(evt) {

	var tgt = evt.target;
	while (true) {
		if (tgt.hasAttribute('data-vrf_id')) {
			break;
		}
		tgt = tgt.parentElement;
	}
	var vrf_id = tgt.getAttribute('data-vrf_id');

	// Find VRF object - it should be in vrf_list
	var vrf = vrf_list[vrf_id];

	if (!selected_vrfs.hasOwnProperty(String(vrf.id))) {

		// Clicked a VRF which was not previously selected - add to filter list
		$.ajax({
			type: "POST",
			url: '/xhr/add_current_vrf',
			data: JSON.stringify({ 'vrf_id': String(vrf.id) }),
			contentType: "application/json"
		});
		selected_vrfs[String(vrf.id)] = vrf;

		// show tick mark
		$('#vrf_filter_entry_' + String(vrf.id)).children().children('.selector_tick').html('&#10003;');
		$('#vrf_filter_entry_' + String(vrf.id)).children('.selector_x').html('<img src="/images/x-mark-3-16.png">');

	} else {

		// Clicked a VRF which was selected - remove from filter list
		delete selected_vrfs[String(vrf.id)];
		$.ajax({
			type: "POST",
			url: '/xhr/del_current_vrf',
			data: JSON.stringify({ 'vrf_id': String(vrf.id) }),
			contentType: "application/json"
		});

		// remove tick mark
		$('#vrf_filter_entry_' + String(vrf.id)).children().children('.selector_tick').html('&nbsp;');
		$('#vrf_filter_entry_' + String(vrf.id)).children('.selector_x').html('');

	}

	drawVRFHeader();
	// Don't perform search if we are not on the prefix list page or if the
	// query string is empty
	if (current_page == 'prefix_list' && $('#query_string').val() != '') {
		performPrefixSearch(true);
	}

	$('.selector_selectedbar').show();
	evt.preventDefault();

}

/*
 * Draw the VRF page header
 */
function drawVRFHeader() {

	// Any VRFs before?
	var first_vrf = $("#first_vrf_filter_entry").attr('data-vrf');

	var n = 0;
	var first_vrf_active = selected_vrfs.hasOwnProperty(first_vrf);
	var second_vrf_active = selected_vrfs.hasOwnProperty(first_vrf);
	$.each(selected_vrfs, function (k, v) {

		// Do we need to replace the first displayed VRF?
		if (n == 0 && !first_vrf_active) {
			$("#first_vrf_filter_entry").html(v.rt == null ? v.name : v.rt);
			$("#first_vrf_filter_entry").attr('data-vrf', String(v.rt));
		}

		// Do we need to replace the second displayed VRF?
		if (n == 1 && !second_vrf_active) {
			$("#second_vrf_filter_entry").html(' and ' + (v.rt == null ? v.name : v.rt));
			$("#second_vrf_filter_entry").attr('data-vrf', String(v.rt));
		}

		n++;

	});

	if (n == 0) {
		$("#first_vrf_filter_entry").html("");
		$("#first_vrf_filter_entry").attr('data-vrf', '');
		$("#second_vrf_filter_entry").hide()
	} else if (n == 1) {
		$("#second_vrf_filter_entry").hide()
		$("#extra_vrf_filter_entry").hide();
	} else if (n == 2) {
		$("#second_vrf_filter_entry").show();
		$("#extra_vrf_filter_entry").hide();
	} else {
		$("#second_vrf_filter_entry").hide()
		$('#extra_vrf_filter_entry').html('and ' + (n - 1) + ' more');
		$("#extra_vrf_filter_entry").show();
	}

}

/*
 * Receive list of currently selected VRFs
 */
function receiveCurrentVRFs(data) {

	selected_vrfs = data;
	jQuery.extend(vrf_list, data);
	drawVRFHeader();

	// Now that we have loaded the selected VRFs, perform prefix search if we
	// are on the prefix list page.
	if (current_page == 'prefix_list') {
		performPrefixSearch();
	}

}


/*
 * Hide any popup menu
 */
function hidePopupMenu() {
	$(".popup_menu").remove();
	$(".popup_overlay").hide();
}


function parseInterp(query, container) {

	if (query.interpretation) {
		var interp = query.interpretation;
		var text = '<b>' + interp.string + ':</b> ' + (interp.interpretation || '');
		var tooltip = '';

		// "Major" parser error - unable to parse string
		if (interp.error === true && interp.operator === null) {
			text += interp.error_message;
			if (interp.error_message == 'unclosed quote') {
				text += ', please close quote!';
				tooltip = 'This is not a proper search term as it contains an uneven amount of quotes.';
			} else if (interp.error_message == 'unclosed parentheses') {
				text += ', please close parentheses!';
				tooltip = 'This is not a proper search term as it contains an uneven amount of parentheses.';
			} else {
				text += '.';
				tooltip = 'Invalid search term.';
			}
		} else if (interp.interpretation == 'or') {
			text = "<b>OR</b>";
		} else if (interp.interpretation == 'and') {
			text = "<b>AND</b>";
		} else if (interp.attribute == 'tag' && interp.operator == 'equals_any') {
			text += ' must contain <b>' + interp.string.slice(1) + '</b>';
			tooltip = "The tag(s) or inherited tag(s) must contain " + interp.string.slice(1);
		} else if (interp.attribute == 'prefix' && interp.operator == 'contained_within_equals') {
			text += ' within ';
			if ('strict_prefix' in interp && 'expanded' in interp) {
				text += '<b>' + interp.strict_prefix + '</b>';
				tooltip = 'Prefix must be contained within ' + interp.strict_prefix + ', which is the base prefix of ' + interp.expanded + ' (automatically expanded from ' + interp.string + ')';
			} else if ('strict_prefix' in interp) {
				text += '<b>' + interp.strict_prefix + '</b>';
				tooltip = 'Prefix must be contained within ' + interp.strict_prefix + ', which is the base prefix of ' + interp.string + '.';
			} else if ('expanded' in interp) {
				text += '<b>' + interp.expanded + '</b>';
				tooltip = 'Prefix must be contained within ' + interp.expanded + ' (automatically expanded from ' + interp.string + ').';
			} else {
				text += '<b>' + interp.string + '</b>';
				tooltip = 'Prefix must be contained within ' + interp.string;
			}
		} else if (interp.attribute == 'prefix' && interp.operator == 'contains_equals') {
			text = '<b>' + interp.string + ':</b> ' + 'Prefix that contains ' + interp.string;
			tooltip = "The prefix must contain or be equal to " + interp.string;
		} else if (interp.attribute == 'prefix' && interp.operator == 'equals') {
			text += ' equal to <b>' + interp.string + '</b>';
			tooltip = "The " + interp.interpretation + " must equal " + interp.string;
		} else if (interp.interpretation == 'expression') {
			text += ", '" + interp.attribute + "' " + operator_map[interp.operator] + " value";
			tooltip += "The attribute '" + interp.attribute + "' must be " + operator_map[interp.operator] + " to provided value.";
		} else {
			text += " matching '<b>" + interp.string + "</b>'";
			tooltip = "The description OR node OR order id OR the comment should regexp match '" + interp.string + "'";
		}

		// Attach "minor" error - could parse string, but contained errors
		if (interp.error === true && interp.operator !== null) {
			if (interp.error_message == 'invalid value') {
				text += ", invalid value!";
				tooltip += "The value provided is not valid for the attribute '" + interp.attribute + "'.";
			} else if (interp.error_message == 'unknown attribute') {
				text += ", unknown attribute '" + interp.attribute + "'!";
				tooltip += "There is not prefix attribute '" + interp.attribute + "'";
			} else {
				text += ", " + interp.error_message + "!";
			}
		}

		if (interp.interpretation == 'or' || interp.interpretation == 'and') {
			var andor_text = $('<div class="search_interpretation" style="display: inline-block; vertical-align: top;"></div>').appendTo(container);
			container = $('<div class="search_interpretation" style="display: inline-block;"></div>').appendTo(container);
			$('<div class="search_interpretation" id="' + container.attr('id') + '_intp" uib-tooltip="' + tooltip + '" style="padding-top: 0.5em; display: inline-block;"><div style="display: inline-block;">' + text + '</div><div style="display: inline-block; border-left:2px solid #666; border-top:2px solid #666; border-bottom:2px solid #666; margin-top: 3px; margin-left: 4px; margin-right: 4px;">&nbsp;</div></div>').appendTo(andor_text);
		} else {
			$('<div class="search_interpretation" style="display: block;" id="' + container.attr('id') + '_intp" uib-tooltip="' + tooltip + '">' + text + '</div>').appendTo(container);
		}
	}

	if (typeof(query.val1) == 'object') {
		parseInterp(query.val1, container);
	}
	if (typeof(query.val2) == 'object') {
		parseInterp(query.val2, container);
	}
}


/*
 * Callback function called when prefixes are received.
 * Plots prefixes and adds them to list.
 */
function receivePrefixList(search_result) {

	stats.response_received = new Date().getTime();

	if (!verifyPrefixListResponse(search_result)) return;
	newest_prefix_query = parseInt(search_result.search_options.query_id);

	$('#search_interpretation').html('<table border=0> <tr> <td class="opt_left" id="search_interpretation_text" style="border-bottom: 1px dotted #EEEEEE;" uib-tooltip="This shows how your search query was interpreted by the search engine. All terms are ANDed together."> Search interpretation </td> <td class="opt_right" id="search_interpret_container" style="border-bottom: 1px dotted #999999;"> </td> </tr> </table>');
	// Run element through AngularJS compiler to "activate" directives (the
	// AngularUI/Bootstrap tooltip)
	$(".search_interpretation_text").replaceWith(ng_compile($(".search_interpretation_text"))(ng_scope));

	/*
	 * Interpretation list
	 */
	var intp_cont = $("#search_interpret_container");
	intp_cont.empty();
	parseInterp(search_result.interpretation, intp_cont);

	// Run element through AngularJS compiler to "activate" directives (the
	// AngularUI/Bootstrap tooltip)
	intp_cont.replaceWith(ng_compile(intp_cont)(ng_scope));
	ng_scope.$apply();

	stats.draw_intp_finished = new Date().getTime();

	/*
	 * Prefix list
	 */
	// clean up old stuff
	$('#prefix_list').empty();
	prefix_list = new Object();
	indent_head = new Object();

	if (search_result.result.length > 0) {

		// insert prefix list
		insertPrefixList(search_result.result);

	} else {

		// No prefixes received
		$('#prefix_list').html('<div style="text-align: center; padding: 30px; color: #777777;">No prefixes found.</div>');

	}

	// Display search statistics
	stats.finished = new Date().getTime();
	showSearchStats(stats);

	// Page full?
	if (!pageFilled()) {
		// Nope. Perform a nextPage()
		performPrefixNextPage();
	}

	// less than max_result means we reached the end of the result set
	if (search_result.result.length < search_result.search_options.max_result) {
		end_of_result = 1;
		$('#nextpage').hide();
	} else {
		$('#nextpage').show();
	}

}


/*
 * Receive a prefix list update.
 */
function receivePrefixListUpdate(search_result, link_type) {

	stats.response_received = new Date().getTime();

	if (!verifyPrefixListResponse(search_result)) return;
	newest_prefix_query = parseInt(search_result.search_options.query_id);

	pref_list = search_result.result;

	// If we got result from a search-operation with a parent_prefix set, we're
	// not guaranteed a result list which is guaranteed to begin with a prefix
	// which we've already received.
	if (search_result.search_options.parent_prefix == null) {
		if (!prefix_list.hasOwnProperty(pref_list[0].id)) {
			pref_list.unshift(prefix_list[search_result.search_options.parent_prefix]);
		}
	}

	// Zero result elements. Should not happen as we at least always should
	// get the prefix we select to list, even if it has no children.
	if (pref_list.length == 0) {

		// TODO: Display notice dialog?
		log('Warning: no prefixes returned from list operation.');
		return true;

	}

	insertPrefixList(pref_list);

	// Display search statistics
	stats.finished = new Date().getTime();
	showSearchStats(stats);

	// As the user pressed the expand button, they probably want to see as much
	// as possible of the prefix they expanded. Therefore, unhide all hidden
	// prefixes.
	unhide($("#collapse" + pref_list[0].id).children(".prefix_hidden_container").attr('data-prefix-id'));

	// Finally, expand the collapsed container!
	expandGroup(pref_list[0].id);

}


/*
 * Receive the "next page" of a prefix list
 */
function receivePrefixListNextPage(search_result) {

	stats.response_received = new Date().getTime();

	hideLoadingIndicator();
	if (!verifyPrefixListResponse(search_result)) return;
	newest_prefix_query = parseInt(search_result.search_options.query_id);

	pref_list = search_result.result;

	// Zero result elements. Should not happen as we at least always should
	// get the last prefix currently listed
	if (pref_list.length == 0) {

		// TODO: Display notice dialog?
		log('Warning: no prefixes returned from list operation.');
		outstanding_nextpage = 0;
		return true;

	// less than max_result means we reached the end of the result set
	} else if (pref_list.length < search_result.search_options.max_result) {

		end_of_result = 1;
		outstanding_nextpage = 0;
		$('#nextpage').hide();

	}

	insertPrefixList(pref_list);
	outstanding_nextpage = 0;

	// Display search statistics
	stats.finished = new Date().getTime();
	showSearchStats(stats);

	// Page full or end of search result reached?
	if (!pageFilled() && end_of_result == 0) {
		// Nope. Perform a nextPage()
		performPrefixNextPage();
	}

}

/*
 * Verify that response from smart_search_prefix is OK
 */
function verifyPrefixListResponse(search_result) {

	// Error?
	if ('error' in search_result) {
		showDialogNotice("Error", search_result.message);
		return false;
	}

	// If we receive a result older than the one we display, ignore the
	// received result.
	if (parseInt(search_result.search_options.query_id) < parseInt(newest_prefix_query)) {
		log("Discarding result " + search_result.search_options.query_id + ", latest query is " + newest_prefix_query);
		return false;
	}

	return true;

}

/*
 * Display search statistics
 */
function showSearchStats(stats) {

	$('#search_stats').html('Query took ' + (stats.response_received - stats.query_sent)/1000 + ' seconds.');
	log('Rendering took ' + (stats.finished - stats.response_received) + ' milliseconds');
}


/*
 * Translate form search options to depth levels
 */
function optToDepth(opt) {

	switch (opt) {
		case 'none': return 0;
		case 'immediate': return 1;
		case 'all': return -1;
		default: return 0;
	}

}

/*
 * Check if the prefix list fills the entire page
 */
function pageFilled() {

	// Do we still have space left on the screen?
	// get current visible part of screen
	var w_height = $(window).height();
	var w_top = $(window).scrollTop();
	var w_bottom = w_top + w_height;

	// get location of element
	e_top = $(".prefix_list").offset().top;
	e_bottom = e_top + $(".prefix_list").height();

	return e_bottom > w_bottom;

}

/*
 * Insert a list of prefixes
 */
function insertPrefixList(pref_list) {

	var prefix = null;
	var prev_prefix = null;

	// return if we did not get any prefixes
	if (pref_list.length == 0) {
		return;
	}

	// Handle first prefix
	prefix = pref_list[0];
	if ($("#prefix_entry" + prefix.id).length > 0) {

		// First prefix already in list
		prev_prefix = prefix_list[prefix.id];

	} else {

		// This should only happen when adding the very first prefix to a completely empty list
		// Add it manually so we have a starting point
		var c = getVRFContainer(prefix.vrf_id);
		showPrefix(prefix, c, null);
		prev_prefix = prefix;
		prefix_list[prefix.id] = prefix;

	}

	// iterate received prefixes
	for (i = 1; i < pref_list.length; i++) {

		// Add prefix to global prefix list object if it's not already there
		prefix = pref_list[i];
		if (!(prefix.id in prefix_list)) {
			prefix_list[prefix.id] = prefix;
		}

		// Add prefix to prefix list if it's not already there (is this redundant to the operation above..?)
		if ($("#prefix_entry" + prefix.id).length == 0) {
			insertPrefix(prefix, prev_prefix);
		}

		// If the current prefix was not added to a hidden container and the
		// last prefix was added to a hidden container, unhide if there are not
		// very many prefixes in it
		// check if current prefix is not hidden
		if (!$("#prefix_entry" + prefix.id).parent().hasClass("prefix_hidden_container")) {
			// was the last prefix
			var p_parent = $("#prefix_entry" + prev_prefix.id).parent();
			if (parseInt(p_parent.find('.prefix_entry').length) < 4) {
				unhide( p_parent.attr('data-prefix-id') );
			}
		}

		prev_prefix = prefix;

	}

}

/*
 * Insert a single prefix into the prefix list
 *
 * Once there was a lengthy explanation of the logic behind how this is done,
 * but nowadays the code should be quite readable. The code below is quite
 * involved though, as there are many cases to take into account...
 */
function insertPrefix(prefix, prev_prefix) {

	var main_container = null;
	var reference = null;
	var offset = null;

	// Changing VRF - create new VRF container and add prefix to it
	if (prefix.vrf_id != prev_prefix.vrf_id) {

		var c = getVRFContainer(prefix.vrf_id);
		showPrefix(prefix, c, null);
		return;

	}

	if (prefix.indent > prev_prefix.indent) {
		// Indent level increased

		main_container = $("#collapse" + prev_prefix.id);

		// if we have a match, add directly to top of main container.
		if (prefix.match) {
			reference = main_container;
			offset = 'prepend';
		} else {
			// No match, add to hidden container. Is there already one?
			if (main_container.children().length == 0) {
				// Nothing at all. Add new hidden container to main_container.
				reference = addHiddenContainer(prefix, main_container, null);
				offset = null;
			} else {
				if (main_container.children(':first').hasClass('prefix_hidden_container')) {
					reference = main_container.children(':first');
					offset = 'prepend';
				} else {
					// add hidden container
					reference = addHiddenContainer(prefix, main_container, 'prepend');
					offset = null;
				}
			 }
		}

		// If prefix has children, do not hide it! Since we are one indent
		// level under last, the previous prefix is our parent and clearly
		// has children, thus unhide!
		unhide(prev_prefix.id);

		// If previous prefix was assignment and a match, do not expand. This
		// means that host prefixes will be hidden from display unless the user
		// actively shows them.
		if (!(prev_prefix.type == 'assignment' && prev_prefix.match)) {
			expandGroup(prev_prefix.id);
		}

	} else if (prefix.indent < prev_prefix.indent) {
		// Indent level decreased

		/*
		 * Find the collapse container in which the previous prefix was placed.
		 */
		main_container = $("#prefix_entry" + prev_prefix.id);
		vrf_container = getVRFContainer(prefix.vrf_id);
		for (i = prev_prefix.indent - prefix.indent; i > 0; i--) {
			main_container = main_container.parent();

			// The previous prefix on our level might have been placed into a
			// hidden container. If so, get it's parent.
			if (main_container.hasClass('prefix_hidden_container')) {
				main_container = main_container.parent();
			}

			// Safety net - stop iterating if we reached the VRF container
			// which is the highest level.
			if (main_container.parent()[0] === vrf_container[0]) {
				break;
			}

		}

		// OK. Match or no match?
		if (prefix.match) {
			// match. Place directly after main_container
			reference = main_container;
			offset = 'after';
		} else {
			// No match. Place in hidden container - is there one?
			var next = main_container.next();

			if (next.length == 0) {
				// Main container last element, place hidden container after it.
				reference = addHiddenContainer(prefix, main_container, 'after');
				offset = null;
			} else {
				if (next.hasClass('prefix_hidden_container')) {
					// Next element was a hidden container, prepend in it.
					reference = next;
					offset = 'prepend';
				} else {
					// Next element was something else. Create new hidden container.
					reference = addHiddenContainer(prefix, main_container, 'prepend');
					offset = null;
				}
			}
		}

		// If we exited a hidden container, see how many prefixes there are in
		// it.
		if (!prev_prefix.match) {
			var p_parent = $("#prefix_entry" + prev_prefix.id).parent();
			if (parseInt(p_parent.children('.prefix_entry').length) <= 4) {
				unhide( p_parent.attr('data-prefix-id') );
			}
		}

	} else {
		// Indent level equal

		if (prev_prefix.match == false && prefix.match == true) {

			// Switching into a match from a non-match, so we should display a
			// "expand upwards" arrow. Place after the element after previous
			// prefix's parent (the hidden container's text).
			reference = $("#prefix_entry" + prev_prefix.id).parent().next();
			offset = 'after';

			// if there are not very many elements in hidden container, show it
			if (reference.children(".prefix_entry").length <= 4) {
				unhide(reference.attr('data-prefix-id'));
			}

		} else if (prev_prefix.match == true && prefix.match == false) {

			// switching into a non-match from a match, so we should display a "expand downwards" arrow
			// create new hidden container in previous prefix's parent (the collapse container)

			// Does container already exist?
			var next = $("#prefix_entry" + prev_prefix.id).next();
			if (next.length == 0) {
				// create new if there is no next element or the next element is not a hidden container
				reference = addHiddenContainer(prefix, $("#prefix_entry" + prev_prefix.id), 'after');
				offset = null;
			} else {
				// There are elements after the previous one. Is it a hidden container?
				if (next.hasClass('prefix_hidden_container')) {
					reference = next;
					offset = 'prepend';
				} else {
					// Next element wasn't hidden container. Add new before next prefix element.
					// As next element was not a hidden container, it can be either a prefix
					// entry or a collapse container.
					// Add before prefix entry and after collapse container.
					if (next.hasClass('prefix-entry')) {
						offset = 'before';
					} else {
						offset = 'after';
					}
					reference = addHiddenContainer(prefix, next, offset);
					offset = null;
				}
			}

		} else {
			// match unchanged - add to previous container
			// EVEN EASIER (AND BETTER) - add after previous prefix
			reference = $("#prefix_entry" + prev_prefix.id);
			if (reference.next().hasClass('prefix_collapse')) {
				reference = reference.next();
			}
			offset = 'after';
		}

	}

	showPrefix(prefix, reference, offset);

}

/*
 * Returns a prefix container for a VRF
 *
 * Creates a new container if it does not exists, otherwise returns the
 * existing one.
 */
function getVRFContainer(vrf_id) {
	if ($('#preflist_prefix_panel_' + vrf_id).length == 0) {
		$.ajax({
			type: "POST",
			url: "/xhr/smart_search_vrf",
			data: JSON.stringify({ 'vrf_id': vrf_id, 'query_string': '' }),
			success: receiveVRFContainerData,
			dataType: "json",
			contentType: "application/json"
		});
		$("#prefix_list").append('<div class="preflist_vrf_container" id="preflist_vrf_container_' + vrf_id + '">' +
			'<div class="preflist_vrf_panel"></div>' +
			'<div class="preflist_prefix_panel" id="preflist_prefix_panel_' + vrf_id + '"></div>' +
			'</div>');
	}

	return $('#preflist_prefix_panel_' + vrf_id);
}

/*
 * Update VRF container with RT and name
 */
function receiveVRFContainerData(search_result) {
	vrf = search_result.result[0];

	$('#preflist_vrf_container_' + vrf.id).children('div[class="preflist_vrf_panel"]').html('<div class="preflist_vrf_rt"><b>RT:&nbsp;' + ( vrf.rt == null ? '-' : vrf.rt ) + '</b></div><b class="t"></b><div class="preflist_vrf_name">' + vrf.name + '</div>');
}

/*
 * Update VRF container with RT and name for add prefix page
 */
function receivePrefixVRFData(search_result) {
	vrf = search_result.result[0];

	$("#prefix_vrf_display").html('<div class="vrf_filter_entry"><div class="vrf_filter_entry_rt">RT:&nbsp;' + vrf.rt + '</div><div class="selector_entry_name" style="margin-left: 5px;">' + vrf.name + '</div><div class="selector_entry_description" style="clear: both;">' + vrf.description + '</div></div>');
    $("#prefix_vrf_display").show();
}


/*
 * Add a container for hidden prefixes
 *
 * Use the options 'relative' and 'offset' to determine where to place the
 * hidden container. 'reference' should be an object which will be used as
 * reference for the placement and 'offset' determines where how to offset the
 * new object relative to 'reference'.
 *
 * 'offset' can take the following values:
 * append - append element into reference
 * prepend - prepend element into reference
 * before - place element before reference
 * after - place element after reference
 */
function addHiddenContainer(prefix, reference, offset) {

	if ($("#prefix_entry" + prefix.id).length > 0) {
		// prefix already exists. Return something.
		// aaargh, this is not clean :( Should be determined elsewhere!
		return $("#prefix_entry" + prefix.id).parent();
	}

	var hcont = '<div id="prefix_hidden_container' + prefix.id + '" class="prefix_hidden_container" data-prefix-id="' + prefix.id + '"></div>';

	if (offset == null || offset == 'append') {
		reference.append(hcont);
	} else if (offset == 'before') {
		reference.before(hcont);
	} else if (offset == 'after') {
		reference.after(hcont);
	} else if (offset == 'prepend') {
		reference.prepend(hcont);
	} else {
		log("Invalid offset: " + offset);
	}

	var container = $('#prefix_hidden_container' + prefix.id);
	container.after('<a id="prefix_hidden_text' + prefix.id + '" class="prefix_hidden_text" style="padding-left: ' + (10 + parseInt(prefix.indent) * 30) + 'px;" href="javascript:void(0);" onclick="unhide(' + prefix.id + ');">(hidden prefixes, click to display)</a>');

	return container;
}


/*
 * Function which is run when a collapse +/- sign is clicked.
 */
function collapseClick(id) {

	var col = $('#collapse' + id);

	if (col.css('display') == 'none') {
		var search_q = jQuery.extend({}, current_query);
		search_q.query_id = query_id;
		search_q.parent_prefix = id;
		search_q.include_parents = false;
		search_q.include_children = false;
		search_q.children_depth = 1;
		search_q.parents_depth = 0;
		search_q.max_result = false;
		search_q.offset = 0;
		delete search_q.indent;

		query_id += 1;

		// Keep track of search timing
		stats.query_sent = new Date().getTime();

		$.ajax({
			type: "POST",
			url: "/xhr/smart_search_prefix",
			data: JSON.stringify(search_q),
			success: receivePrefixListUpdate,
			dataType: "json",
			contentType: "application/json"
		});

	} else {
		collapseGroup(id);
	}
}

/*
 * Expand a container containing hidden prefixes and remove the "show" link
 */
function unhide(id) {
	$('#prefix_hidden_container' + id).slideDown();
	$('#prefix_hidden_text' + id).remove();
}


/**********************************************************************
 *
 * Add prefix functions
 *
 *********************************************************************/

/*
 * Show prefix allocation container depending on what allocation
 * method is chosen.
 */
function showAllocContainer(e) {

	$("input[name = prefix_vrf]").show();
	// from-prefix
	if (e.currentTarget.id == 'radio-from-prefix') {

		alloc_method = 'from-prefix';

		$("#from-prefix_container").show();
		$("#from-pool_container").hide();
		$("#prefix_data_container").hide();
		$("#prefix-row").hide();
		$("html,body").animate({ scrollTop: $("#from-prefix_container").offset().top - 50}, 700);

		$('#default_prefix_type').hide();
		$('#prefix_type_selection').show();

	// from-pool
	} else if (e.currentTarget.id == 'radio-from-pool') {

		alloc_method = 'from-pool';

		$("#from-prefix_container").hide();
		$("#from-pool_container").show();
		$("#prefix_data_container").hide();
		$("#prefix-row").hide();
		$('#prefix_length_prefix_container').hide();
		$("html,body").animate({ scrollTop: $("#from-pool_container").offset().top - 50}, 700);

	// else - manual
	} else {

		alloc_method = 'manual';

		$("#from-prefix_container").hide();
		$("#from-pool_container").hide();
		$("#prefix-row").show();
		$("#prefix_data_container").show();
		$('#prefix_length_prefix_container').hide();
		$("html,body").animate({ scrollTop: $("#prefix_data_container").offset().top - 50}, 700);

		// VRF handling of manually added prefixes differ between add prefix
		// and add prefix too pool-pages. When adding a prefix to a pool, even
		// manually added prefixes can have the VRF set on beforehand. Check
		// ugly global variable to see what we're currently doing.
		if (prefix_link_type == 'add_too_pool') {
			// Adding a prefix to a pool

			// Do we have an implied VRF set?
			if (typeof(implied_vrf) != 'undefined') {
				if (implied_vrf.id == null) {

					resetPrefixVRFDisplay();

				} else {

					// Set prefix VRF to pool's implied VRF (if available)
					$("#prefix_vrf_text").html("VRF " + implied_vrf.rt + " taken from pool's implied VRF.");
					$("input[name = prefix_vrf]").val(implied_vrf.id);
					$("input[name = prefix_vrf_btn]").hide();
					$("#prefix_vrf_display").html('<div class="vrf_filter_entry"><div class="vrf_filter_entry_rt">RT:&nbsp;' + implied_vrf.rt + '</div><div class="selector_entry_name" style="margin-left: 5px;">' + implied_vrf.name + '</div><div class="selector_entry_description" style="clear: both;">' + implied_vrf.description + '</div></div>');
					$("#prefix_vrf_display").show();

				}
			}

		} else {
			// "Normal" addition of a prefix

			resetPrefixVRFDisplay();

			if (Object.keys(selected_vrfs).length == 0) {
				$("#prefix_vrf_text").html("No VRF currently selected, please choose destination VRF for new prefix manually.");
				$("#prefix_vrf_display").html("No VRF selected.");
			} else if (Object.keys(selected_vrfs).length == 1) {
				var vrf = null;
				$.each(selected_vrfs, function(k, v) { vrf = v; });
				$("#prefix_vrf_text").html('Destination VRF for new prefix set to currently selected VRF.');
				$("#prefix_vrf_display").html('<div class="vrf_filter_entry"><div class="vrf_filter_entry_rt">RT:&nbsp;' + vrf.rt + '</div><div class="selector_entry_name" style="margin-left: 5px;">' + vrf.name + '</div><div class="selector_entry_description" style="clear: both;">' + vrf.description + '</div></div>');
				$('input[name="prefix_vrf_id"]').val(vrf.id);
			} else {
				$("#prefix_vrf_text").html("Multiple VRFs selected, please choose destination VRF for new prefix manually.");
				$("#prefix_vrf_display").html("No VRF selected.");
			}
			$("#prefix_vrf_display").show();
		}

	}

	$('#radio-prefix-type-reservation').removeAttr('disabled');
	$('#radio-prefix-type-assignment').removeAttr('disabled');
	$('#radio-prefix-type-host').removeAttr('disabled');

	$('#radio-prefix-type-reservation').removeAttr('checked');
	$('#radio-prefix-type-assignment').removeAttr('checked');
	$('#radio-prefix-type-host').removeAttr('checked');

	// Re-evaluate node field when prefix length is changed. The same
	// thing for the prefix_length_prefix field is done in the selectPrefix
	// function. From some reason it can not be done here...
	$('input[name="prefix_length_pool"]').keyup(enableNodeInput);

}

/*
 * Reset the VRF display on add prefix pages
 */
function resetPrefixVRFDisplay() {

	// Reset VRF display and enable VRF selector
	$("#prefix_vrf_display").html('');
	$("#prefix_vrf_display").hide();
	$("#prefix_vrf_display").attr('title', '');
	$("input[name = prefix_vrf_btn]").show();

	$('#default_prefix_type').hide();
	$('#prefix_type_selection').show();

}


/*
 * Run whenever the prefix monitor checkbox is toggled.
 * Makes sure that the alarm priority select box is shown when
 * it should be.
 */
function prefixMonitorToggled() {

	if ($('input[name="prefix_monitor"]').is(":checked")) {
		$("#alarm_priority_container").show();
	} else {
		$("#alarm_priority_container").hide();
	}

}

/*
 * Run whenever the prefix type checkbox is toggled.
 */
function prefixTypeToggled(e) {

	// enables/disables monitor and node options
	enableMonitor();
	enableNodeInput();

}

/*
 * Enables/disables monitor options
 */
function enableMonitor() {

	// gray out monitor options when prefix type is host
	if ($('input[name="prefix_type"]:checked').val() == 'host') {
		$('input[name="prefix_monitor"]').attr('disabled', true);
		$('input[name="prefix_alarm_priority"]').attr('disabled', true);
	} else {
		$('input[name="prefix_monitor"]').removeAttr('disabled');
		$('input[name="prefix_alarm_priority"]').removeAttr('disabled');
	}

}


/*
 * Function which determines whether the Node input element should be enabled
 * or not. It is only available when the prefix in question is configured as a
 * node, ie the prefix is a /32 or /128.
 *
 * It's called from the prefix add and prefix edit page and as these pages look
 * somewhat different we need to account for some stuff.
 */
function enableNodeInput() {

	/*
	 * Generally, the node option should only be available for host prefixes.
	 * However, there is one exception: loopbacks, which are defined as
	 * assignments with max prefix length.
	 */

	 // See if prefix type is set
	 var type = $('input[name="prefix_type"]:checked').val();
	 if (type == 'reservation') {

		// reservation - disable no matter what
		$('input[name="prefix_node"]').attr('disabled', true);

	 } else if (type == 'host') {

		// host - enable no matter what
		$('input[name="prefix_node"]').removeAttr('disabled');

	 } else if (type == 'assignment') {

		/*
		 * Assignment - more tricky case!
		 *
		 * Enable if prefix length is max prefix length.
		 *
		 * If we add a prefix from a pool, we have the length in an input
		 * field. Also the family can be fetched from an input field.
		 *
		 * If we add a prefix from another prefix, we can find the prefix
		 * length from the prefix length field and the family from the selected
		 * prefix
		 *
		 * If we add manually, we use a super-regex to determine if it is a
		 * host prefix or not!
		 */

		/* A bit of a hack as this function is used from multiple pages. When
		 * adding a new prefix the alloc_method is already set but on the
		 * prefix edit page, we don't have a alloc_method and so we set it to
		 * 'manual' to kind of emulate the same behaviour.
		 */
		if (typeof(alloc_method) == "undefined") {
			alloc_method = 'manual';
		}

		if (alloc_method == 'from-pool') {

			// fetch prefix length & family
			var len = $('input[name="prefix_length_pool"]').val();
			var family = $('input[name="prefix_family"]:checked').val();

			if (hasMaxPreflen({ 'family': family, 'prefix': '/' + len })) {
				$('input[name="prefix_node"]').removeAttr('disabled');
			} else {
				$('input[name="prefix_node"]').attr('disabled', true);
			}

		} else if (alloc_method == 'from-prefix') {

			// fetch prefix length & family
			var len = $('input[name="prefix_length_prefix"]').val();
			var family = cur_opts.from_prefix.family;

			if (hasMaxPreflen({ 'family': family, 'prefix': '/' + len })) {
				$('input[name="prefix_node"]').removeAttr('disabled');
			} else {
				$('input[name="prefix_node"]').attr('disabled', true);
			}

		} else if (alloc_method == 'manual') {

			// check if what has been inputted in the prefix input is a host
			// prefix or not - see http://jsfiddle.net/AJEzQ/
			if (/^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/32)?$|^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|:)))(\/128)?$/.test($('input[name="prefix_prefix"]').val())) {
				$('input[name="prefix_node"]').removeAttr('disabled');
			} else {
				$('input[name="prefix_node"]').attr('disabled', true);
			}

		}

	 } else {

		// not set - disable
		$('input[name="prefix_node"]').attr('disabled', true);

	 }


}

/*
 * Is run when the adress family is changed
 */
function changeFamily() {

	// set prefix length in pool length input
	if (alloc_method == 'from-pool') {

		var len = null;
		var family = null;

		if ($('input[name="prefix_family"]:checked').val() == '4') {
			len = cur_opts.pool.ipv4_default_prefix_length;
		} else {
			len = cur_opts.pool.ipv6_default_prefix_length;
		}

		// The default length can be null. Handle!
		if (len == null) {
			// TODO: This never happens. I guess the JSON conversion removes the null values.
			$('#edit_length_default_radio').hide();
			$('#def_length_container').hide();
			$("#edit_length_override_radio").click();
		} else {
			$('#edit_length_default_radio').show();
			$("#edit_length_default_radio").click();
			$('#def_length_container').show();
			$('input[name="prefix_length_pool"]').val(len);
			$('#def_length_container').html("Use pool's default IPv" +
				$('input[name="prefix_family"]:checked').val() + " prefix-length of /" +
				len + ".");
		}

	}

	enableNodeInput();

	// TODO: set prefix length in prefix input

}


/*
 * Populate the pool table with JSON data
 */
function populatePoolTable(data) {

	var pool_table_data = [];

	for (key in data) {

		// Save pool object to pool list
		pool_list[data[key].id] = data[key];

		if (data[key].ipv4_default_prefix_length == null) {
			var v4 = '-';
		} else {
			var v4 = data[key].ipv4_default_prefix_length;
		}
		if (data[key].ipv6_default_prefix_length == null) {
			var v6 = '-';
		} else {
			var v6 = data[key].ipv6_default_prefix_length;
		}

		var link = '<a href="javascript:void(0);" onClick="selectPool(' + data[key].id + ');">' + data[key].name + '</a>';

		var pool = [ link, data[key].description, data[key].default_type, v4 + ' / ' + v6 ];

		pool_table_data.push(pool);

	}

	// Enable pool dataTable
	$('#pool_table').dataTable({
		'bAutoWidth': false,
		'bDestroy': true,
		'bPaginate': false,
		'bSortClasses': false,
		'aaData': pool_table_data,
		'aoColumns': [
			null, // name
			null, // description,
			{ 'sWidth': '110px' }, // default type
			{ 'sWidth': '80px' } // default prefix length
		]
	});

}


/*
 * Run when a pool is selected from the pool list.
 */
function selectPool(id) {

	// Save the pool
	cur_opts.pool = pool_list[id];

	// Set default type
	if (cur_opts.pool.default_type == 'reservation') {
		$('#radio-prefix-type-reservation').prop('checked', true);
	} else if (cur_opts.pool.default_type == 'assignment') {
		$('#radio-prefix-type-assignment').prop('checked', true);
	} else if (cur_opts.pool.default_type == 'host') {
		$('#radio-prefix-type-host').prop('checked', true);
	}

    // Set prefix VRF to pool's implied VRF (if available)
    if (cur_opts.pool.vrf_rt == null) {
        $("input[name = prefix_vrf_id]").val(null);
    } else {
        $("input[name = prefix_vrf_id]").val(cur_opts.pool.vrf_id);
    }

	$("#prefix_vrf_text").html("Destination VRF for new prefix taken from pool's implied VRF.");
	$("#prefix_vrf_display").html('<div class="vrf_filter_entry"><div class="vrf_filter_entry_rt">RT:&nbsp;' + ( cur_opts.pool.vrf_rt == null ? '-' : cur_opts.pool.vrf_rt ) + '</div><div class="selector_entry_name" style="margin-left: 5px;"></div><div class="selector_entry_description" style="clear: both;"></div></div>');
    $("input[name = prefix_vrf_btn]").hide();
    $("#prefix_vrf_display").show();
	$.getJSON("/xhr/smart_search_vrf", { 'vrf_id': cur_opts.pool.vrf_id, 'query_string': '' }, receivePoolImpliedVRFData);


	// show pool name and description
	$('#selected_pool_desc').html(pool_list[id].name + ' &mdash; ' + pool_list[id].description);
	if (pool_list[id].default_type != null) {
		$('#pool_prefix_type').html(pool_list[id].default_type);
		$('#default_prefix_type').show();
		$('#prefix_type_selection').hide();
		$('#prefix-type-res').prop('checked', 'false');
		$('#prefix-type-ass').prop('checked', 'false');
		$('#prefix-type-host').prop('checked', 'false');
		if (pool_list[id].default_type == 'reservation') { $('#prefix-type-res').prop('checked', 'true') }
		if (pool_list[id].default_type == 'assignment') { $('#prefix-type-ass').prop('checked', 'true') }
		if (pool_list[id].default_type == 'host') { $('#prefix-type-host').prop('checked', 'true') }
	}

	// display data form
	$("#prefix_data_container").css('display', 'block');

	// set prefix length
	changeFamily();
	$('#length_info_row').css('display', 'block');
	$('#length_edit_row').css('display', 'inline-block');

	// enable/disable the Node input
	enableNodeInput();

	$("html,body").animate({ scrollTop: $("#length_info_row").offset().top - 50}, 700);
	$("#length_info_row").animate({ backgroundColor: "#ffffff" }, 1).delay(200).animate({ backgroundColor: "#dddd33" }, 300).delay(200).animate({ backgroundColor: "#ffffee" }, 1000);

}


/*
 * Update VRF info based on pools implied_vrf information
 */
function receivePoolImpliedVRFData(search_result) {
	implied_vrf = search_result.result[0];

	$("#prefix_vrf_display").html('<div class="vrf_filter_entry"><div class="vrf_filter_entry_rt">RT:&nbsp;' + ( cur_opts.pool.vrf_rt == null ? '-' : cur_opts.pool.vrf_rt ) + '</div><div class="selector_entry_name" style="margin-left: 5px;">' + implied_vrf.name + '</div><div class="selector_entry_description" style="clear: both;">' + implied_vrf.description + '</div></div>');
}


/*
 * Toggle change of prefix length
 */
function toggleLengthEdit(e) {

	// view input field
	if (e.currentTarget.id == 'edit_length_default_radio') {
		$('#length_row').hide();
	} else {
		$('#length_row').show();
	}

}


/*
 * Perform operation
 */
function prefixFormSubmit(e) {

	e.preventDefault();

	// create prefix data object
	var prefix_data = {
		'description': $('input[name="prefix_description"]').val(),
		'comment': $('textarea[name="prefix_comment"]').val(),
		'inherited_tags': $('input[name="prefix_inherited_tags"]').val(),
		'tags': $('input[name="prefix_tags"]').val(),
		'node': $('input[name="prefix_node"]').val(),
		'type': $('input[name="prefix_type"]:checked').val(),
		'status': $('select[name="prefix_status"]').val(),
		'country': $('input[name="prefix_country"]').val(),
		'order_id': $('input[name="prefix_order_id"]').val(),
		'customer_id': $('input[name="prefix_customer_id"]').val(),
		'vrf': $('input[name="prefix_vrf_id"]').val(),
		'alarm_priority': $('input[name="prefix_alarm_priority"]:checked').val(),
		'vlan': $('input[name="prefix_vlan"]').val()
	};
    prefix_data['tags'] = JSON.stringify($('#tags').tagit('assignedTags'));

	// make sure monitor is disabled for host prefixes
	if (prefix_data.type == 'host') {
		prefix_data.monitor = false;
	} else {
		prefix_data.monitor = $('input[name="prefix_monitor"]').val();
	}

	// Add pool to prefix data if it is available
	if (typeof pool_id != "undefined") {
		prefix_data.pool = pool_id;
	}

	// different data due to different allocation methods
	if (alloc_method == 'from-pool') {

		prefix_data.from_pool = cur_opts.pool.id;
		prefix_data.prefix_length = $('input[name="prefix_length_pool"]').val();
		prefix_data.family = $('input[name="prefix_family"]:checked').val();

	} else if (alloc_method == 'from-prefix') {

		prefix_data.from_prefix = new Array(cur_opts.from_prefix.prefix);
		prefix_data.prefix_length = $('input[name="prefix_length_prefix"]').val();

		// validate the prefix-length
		if (prefix_data.prefix_length == '') {
			showDialogNotice('Invalid prefix-length', 'You must set a prefix-length.');
			return;
		} else if (prefix_data.prefix_length % 1 !== 0) {
			showDialogNotice('Invalid prefix-length', 'Prefix-length must be an integer.');
			return;
		} else if (prefix_list[cur_opts.from_prefix.id].family == 4) {
			if (prefix_data.prefix_length < 1 || prefix_data.prefix_length > 32) {
				showDialogNotice('Invalid prefix-length', 'Prefix-length for IPv4 must be an integer between 1 and 32.');
				return;
			}
		} else if (prefix_list[cur_opts.from_prefix.id].family == 6) {
			if (prefix_data.prefix_length < 1 || prefix_data.prefix_length > 128) {
				showDialogNotice('Invalid prefix-length', 'Prefix-length for IPv6 must be an integer between 1 and 128.');
				return;
			}
		}

	} else {

		prefix_data.prefix = $('input[name="prefix_prefix"]').val();

	}

	$.getJSON('/xhr/add_prefix', prefix_data, prefixAdded);

}


/*
 * Is run when a prefix is selected in the list.
 */
function selectPrefix(prefix_id) {

	// handle different type of parent prefixes
	if (prefix_list[prefix_id].type == 'host') {
		// host, not possible to assign from
		showDialogNotice('Choose another..', "It's not possible to allocate a new prefix from a prefix of type host (it's a /32).");
		return;
	} else if (hasMaxPreflen(prefix_list[prefix_id])) {
		// an assignment or something with /32 or /128 length, not possible to assign from..
		showDialogNotice('Choose another..', "It's not possible to allocate a new prefix from a prefix with a prefix-length of /32.");
		return;
	} else if (prefix_list[prefix_id].type == 'reservation') {
		$('#length_info_text').html('<input type="text" size=3 name="prefix_length_prefix">');

		// enable / disable types
		$('#radio-prefix-type-reservation').removeAttr('disabled');
		$('#radio-prefix-type-assignment').removeAttr('disabled');
		$('#radio-prefix-type-host').attr('disabled', 'disabled');

		$('#radio-prefix-type-host').removeAttr('checked');

	} else if (prefix_list[prefix_id].type == 'assignment') {

		// set prefix length
		if (prefix_list[prefix_id].family == 4) {
			maxpreflen = 32;
		} else {
			maxpreflen = 128;
		}

		$('#length_info_text').html('<span uib-tooltip="The parent prefix is of type assignment, prefix-length of the new prefix will thus be /' + maxpreflen + '.">/' + maxpreflen + '</span><input type="hidden" name="prefix_length_prefix" value=' + maxpreflen+ '>');
		// Run element through AngularJS compiler to "activate" directives (the
		// AngularUI/Bootstrap tooltip)
		$('#length_info_text').replaceWith(ng_compile($('#length_info_text'))(ng_scope));
		ng_scope.$apply();

		// enable / disable types
		$('#radio-prefix-type-reservation').attr('disabled', 'disabled');
		$('#radio-prefix-type-assignment').attr('disabled', 'disabled');
		$('#radio-prefix-type-host').removeAttr('disabled');

		$('#radio-prefix-type-host').prop('checked', true);
	}

	// Set VRF to the same as the prefix we're allocating from
	$.getJSON("/xhr/smart_search_vrf", { 'vrf_id': prefix_list[prefix_id].vrf_id, 'query_string': '' }, receivePrefixVRFData);
	$('input[name="prefix_vrf_id"]').val(prefix_list[prefix_id].vrf_id);

	$("#prefix_vrf_text").html('VRF from parent prefix:');
	$("#prefix_vrf_display").html();
	$("input[name = prefix_vrf_btn]").hide();

	// Lead the user to the next step in the process
	$('#prefix_data_container').show();
	$('#prefix_length_prefix_container').show();

	$('#alloc_from_prefix').html(prefix_list[prefix_id].prefix + ' &mdash; ' + prefix_list[prefix_id].description);
	cur_opts.from_prefix = prefix_list[prefix_id];

	$("html,body").animate({ scrollTop: $("#prefix_length_prefix_container").offset().top - 50}, 700);
	$("#prefix_length_prefix_container").animate({ backgroundColor: "#ffffff" }, 1).delay(200).animate({ backgroundColor: "#dddd33" }, 300).delay(200).animate({ backgroundColor: "#ffffee" }, 1000);

	// Enable keyup action on prefix length input field.
	// From some reason needs to be done here and not when the page is loaded,
	// where it is done for the prefix length field for pools.
	$('input[name="prefix_length_prefix"]').keyup(enableNodeInput);
	enableMonitor();
	enableNodeInput();

}





/**********************************************************************
 *
 * Misc convenience functions
 *
 **********************************************************************/

/*
 * Returns true if prefix has max prefix length.
 */
function hasMaxPreflen(prefix) {

	if ((prefix.family == 4 && parseInt(prefix.prefix.split('/')[1]) == 32) ||
		(prefix.family == 6 && parseInt(prefix.prefix.split('/')[1]) == 128)) {
		return true;
	} else {
		return false;
	}

}

/*
 * Add loading indicator
 */
function showLoadingIndicator(p_container) {

	p_container.append('<div class="loading">&nbsp;</div>');
	$(".loading").fadeIn();

}

/*
 * Hide loading indicator
 */
function hideLoadingIndicator() {

	$(".loading").fadeOut().remove();

}

/*
 * Scroll to place item of interest in view.
 *
 * This function implements a scrolling scheme which tries to avoid
 * scrolling too much, which only annoys the user.
 */
function scrollItemVisible(item) {

	// viewport margin, in part of viewport height
	var w_margin = 0.1;

	// get current visible part of screen
	var w_height = $(window).height();
	var w_top = $(window).scrollTop();
	var w_bottom = w_top + w_height;

	// get location of element
	e_top = item.offset().top;
	e_bottom = e_top + item.height();

	// is element within "visible portion" of screen?
	if (e_top >= w_top + w_margin * w_height && e_bottom <= w_bottom - w_margin * w_height) {

		// Yes! Do nothing!
		return;

	}

	/*
	 * Nope, we need to scroll.
	 *
	 * If the element is placed above the screen, scroll to place it on top of
	 * screen. Also if the element is larger then viewport, place it on top to
	 * make as much of the item as possible visible.
	 *
	 * Otherwise (which should mean that the element is placed below the bottom
	 * of the viewport), scroll to place bottom of item just above bottom of
	 * viewport.
	 */
	if ((e_top < w_top + w_margin * w_height) || (w_height - 2 * w_margin * w_height <= item.height())) {

		// Item is above viewport. Scroll to place it at the top.
		$("html,body").animate({ scrollTop: e_top - w_margin * w_height }, 700);

	} else {

		// item is below viewport. Scroll to place it at the bottom.
		$("html,body").animate({ scrollTop: e_bottom + w_margin * w_height - w_height }, 700);

	}

}
