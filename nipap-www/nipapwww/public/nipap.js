/**********************************************************************
 *
 * NIPAP JavaScript functions
 *
 *********************************************************************/

/**
 * Global variables...
 */
var schema_id = 0;

/*
 * The prefix_list variable is used to keep a copy of all the prefixes
 * currently in the displayed list. Before adding, they are given a new
 * attribute: children. It is used to save information regarding
 * whether the prefix has children or not. These values are allowed:
 *  -2: We have no clue
 *  -1: At least one, but might be more (used for parent prefixes which
 *	  was received when a prefix further down was requested including
 *	  parents)
 *   0: No children
 *  >0: Has children
 */
var prefix_list = Object();
var pool_list = new Object();
var indent_head = Object();

// Object for storing statistics
var stats = Object();

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

// Max prefix lengths for different address families
var max_prefix_length = [32, 128];

var current_query = {
	'query_string': '',
	'parents_depth': 0,
	'children_depth': 0
};
var query_id = 0;
var newest_query = 0;

var offset = 0;
var outstanding_nextpage = 0;
var end_of_result = 0;

var search_key_timeout = 0;

// store current container for inserting prefixes
var container = null;

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
				$(this).parents(".ui-dialog:first").find(":button:eq(0)").addClass("button button_green");
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
function showDialogYesNo(title, msg, target) {
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
				// XXX: this is a bloody hack to override the jquery ui CSS
				//		classes, or rather remove them and have our standard
				//		button look instead
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-state-default");
				$(this).parents(".ui-dialog:first").find(":button").removeClass("ui-state-focus");
				$(this).parents(".ui-dialog:first").find(":button:eq(0)").addClass("button button_red");
				$(this).parents(".ui-dialog:first").find(":button:eq(1)").addClass("button button_green");
			},
			modal: true,
			title: title,
			buttons: [
				{
					style: 'margin: 10px; width: 50px;',
					text: "Yes",
					click: target,
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
		   "<h3>Examples</h3>" +
		   "To find what the IP address 192.168.1.1 is used for:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;192.168.1.1" +
		   "<br/><br/>To list all addresses inside 172.16.0.0/24:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;172.16.0.0/24" +
		   "<br/><br/>To match prefixes with 'TEST-ROUTER-1' in description or comment and that are somewhere in the network 10.0.0.0/8:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;10.0.0.0/8 TEST-ROUTER-1" +
		   '<br/><br/></div>';

	d = showDialog('search_help', 'Searching', c, 800);

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
 * Toggles a collapse group
 */
function toggleGroup(id) {

	var col = $('#collapse' + id);

	if (col.css('display') == 'none') {
		expandGroup(id);
	} else {
		collapseGroup(id);
	}

}

/*
 * Expands a collapse group
 */
function expandGroup(id) {

	var col = $('#collapse' + id);
	var exp = $('#prefix_exp' + id);

	col.slideDown();
	if (prefix_list[id].children < 0) {
		// there might be additional children, display a +!
		exp.html('+');
	} else {
		exp.html('&ndash;');
	}

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
	$('#prefix_list').empty();
	$('#search_interpret_container').empty();
	$('#search_result_help').show();
	$('#nextpage').hide();
	query_id += 1;

	current_query = {
		'query_string': '',
		'parents_depth': 0,
		'children_depth': 0
	};
}

/*
 * Wrapper for pacing our searches somewhat
 *
 * 200ms works out to be a pretty good delay for a fast typer
 */
function prefixSearchKey() {
	clearTimeout(search_key_timeout);
	search_key_timeout = setTimeout("performPrefixSearch()", 200);
}

/*
 * Perform a search operation
 */
function performPrefixSearch(explicit) {
	if (explicit != true) {
		explicit = false;
	}

	// Skip search if query string empty
	if (jQuery.trim($('#query_string').val()).length < 1) {
		clearPrefixSearch();
		return true;
	}
	end_of_result = 0;

	// Keep track of search timing
	stats.query_sent = new Date().getTime();

	var search_q = {
		'query_id': query_id,
		'query_string': $('#query_string').val(),
		'schema': schema_id,
		'parents_depth': optToDepth($('input[name="search_opt_parent"]:checked').val()),
		'children_depth': optToDepth($('input[name="search_opt_child"]:checked').val()),
		'include_all_parents': 'true',
		'include_all_children': 'false',
		'max_result': 50,
		'offset': 0
	}

	// Skip search if it's equal to the currently displayed search
	if (
		(search_q.query_string == current_query.query_string &&
		 search_q.parents_depth == current_query.parents_depth &&
		 search_q.children_depth == current_query.children_depth)
		 && explicit == false) {
		return true;
	}


	current_query = search_q;
	query_id += 1;
	offset = 0;

	$('#prefix_list').empty();
	$('#search_result_help').hide();

	showLoadingIndicator($('#prefix_list'));
	$.getJSON("/xhr/smart_search_prefix", current_query, receivePrefixList);

	// add search options to URL
	setSearchPrefixURI(explicit);

}


/*
 * Extract search options and add to URI
 */
function setSearchPrefixURI(explicit) {

	var url = $.url();
	var url_str = "";

	url_str = url.attr('protocol') + '://' + url.attr('host');

	if (url.attr('port') != null) {
		url_str += ":"+url.attr('port');
	}

	url_str += url.attr('path');

	if (url.attr('query') != null) {
		url_str += '?' + url.attr('query');
	}

	url_str += '#query_string=' +
		encodeURIComponent($('#query_string').val()) +
		'&search_opt_parent=' +
		encodeURIComponent($('input[name="search_opt_parent"]:checked').val()) +
		'&search_opt_child=' +
		encodeURIComponent($('input[name="search_opt_child"]:checked').val()) +
		'&explicit=' + encodeURIComponent(explicit);

	window.location.href = url_str;

}


/*
 * Called when next page of results is requested by the user.
 */
function performPrefixNextPage () {
	if (outstanding_nextpage == 1 || end_of_result == 1 ||
		jQuery.trim($('#query_string').val()).length < 1) {
		return;
	}
	outstanding_nextpage = 1;

	offset += 49;

	current_query.query_id = query_id;
	current_query.offset = offset;

	query_id += 1;

	$.getJSON("/xhr/smart_search_prefix", current_query, receivePrefixListNextPage);

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
	if (prefix.children == 0 || hasMaxPreflen(prefix)) {

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
			prefix.id + '&schema=' + schema_id + '" onClick="addToPool(' + prefix.id +
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
	prefix_type_icon.addClass('tooltip');
	prefix_type_icon.attr('title', prefix.type[0].toUpperCase() + prefix.type.slice(1));
	prefix_type_icon.html(prefix.type[0].toUpperCase());

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

	// Add VRF
	prefix_row.append('<div id="prefix_vrf' + prefix.id + '">');
	var prefix_vrf = $('#prefix_vrf' + prefix.id);
	prefix_vrf.addClass('prefix_column');
	prefix_vrf.addClass('prefix_vrf');
	if (prefix.vrf == null || prefix.vrf == '') {
		prefix_vrf.html("&nbsp;");
	} else {
		prefix_vrf.html(prefix.vrf);
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
 * Function which is ran when a prefix has been removed
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
function getPopupMenu(button, name_prefix, data_id) {

	// Add prefix menu
	var name = 'popupmenu_' + name + '_' + data_id;
	$('body').append('<div id="' + name + '">');
	var menu = $('#' + name);
	menu.addClass("popup_menu");
	menu.html("<h3>" + name_prefix + " menu</h3>");

	// show overlay
	$('body').append('<div class="popup_menu_overlay"></div>');
	$(".popup_menu_overlay").click(function() { hidePopupMenu() });
	$(".popup_menu_overlay").show();

	// Set menu position
	menu.css('top', button.offset().top + button.height() + 5 + 'px');
	menu.css('left', button.offset().left + 'px');

	return menu;
}

/*
 * Show the prefix menu
 */
function showPrefixMenu(prefix_id) {

	// Add prefix menu
	var button = $('#prefix_button' + prefix_id);
	var menu = getPopupMenu(button, 'prefix', prefix_id);

	// Add different manu entries depending on where the prefix list is displayed
	if (prefix_link_type == 'select') {
		// select prefix (allocate from prefix function on add prefix page)
	} else if (prefix_link_type == 'add_to_pool') {
		// Add to pool (Add prefix to pool on edit pool page)
	} else {
		// ordinary prefix list
		menu.append('<a href="/prefix/edit/' + prefix_id + '?schema=' + schema_id + '">Edit</a>');
		menu.append('<a id="prefix_remove' + prefix_id + '" href="/prefix/remove/' + prefix_id + '?schema=' + schema_id + '">Remove</a>');
		$('#prefix_remove' + prefix_id).click(function(e) {
			e.preventDefault();
			var dialog = showDialogYesNo('Really remove prefix?', 'Are you sure you want to remove the prefix ' + prefix_list[prefix_id].display_prefix + '?',
				function () {
					var data = {
						'schema': schema_id,
						'id': prefix_id
					};
					$.getJSON('/xhr/remove_prefix', data, prefixRemoved);

					hidePopupMenu();
					dialog.dialog('close');

				});

		});
	}


	// show overlay
	$(".prefix_menu_overlay").show();

	// Set menu position
	var button_pos = $('#prefix_button' + prefix_id).position();
	menu.css('top', button_pos.top + $('#prefix_button' + prefix_id).height() + 5 + 'px');
	menu.css('left', button_pos.left + 'px');
	menu.slideDown('fast');

}


/*
 * Hide any popup menu
 */
function hidePopupMenu() {
	$(".popup_menu").remove();
	$(".popup_menu_overlay").hide();
}


/*
 * Callback function called when prefixes are received.
 * Plots prefixes and adds them to list.
 */
function receivePrefixList(search_result) {
	stats.response_received = new Date().getTime();

	if (! ('query_id' in search_result.search_options)) {
		showDialogNotice("Error", 'No query_id');
		return;
	}
	if (parseInt(search_result.search_options.query_id) < parseInt(newest_query)) {
		return;
	}
	newest_query = parseInt(search_result.search_options.query_id);

	// Error?
	if ('error' in search_result) {
		showDialogNotice("Error", search_result.message);
		return;
	}

	/*
	 * Interpretation list
	 */
	var intp_cont = $("#search_interpret_container");
	intp_cont.empty();
	for (key in search_result.interpretation) {

		var interp = search_result.interpretation[key];
		var text = '<b>' + interp.string + ':</b> ' + interp.interpretation;
		var tooltip = '';
		if (interp.interpretation == 'unclosed quote') {
			text += ', please close quote!';
			tooltip = 'This is not a proper search term as it contains an uneven amount of quotes.';
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
		} else if (interp.attribute == 'prefix' && interp.operator == 'equals') {
			text += ' equal to <b>' + interp.string + '</b>';
			tooltip = "The " + interp.interpretation + " must equal " + interp.string;
		} else {
			text += " matching '<b>" + interp.string + "</b>'";
			tooltip = "The description OR node OR order id OR the comment should regexp match '" + interp.string + "'";
		}

		intp_cont.append('<div class="search_interpretation tooltip" id="intp' + key + '" title="' + tooltip + '">');
		$('#intp' + key).html(text);
		$('#intp' + key).tipTip({delay: 100});

	}
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

	stats.finished = new Date().getTime();

	// Display search statistics
	log('Rendering took ' + (stats.finished - stats.response_received) + ' milliseconds');
	$('#search_stats').html('Query took ' + (stats.response_received - stats.query_sent)/1000 + ' seconds.');

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
 *
 * This function assumes that the first element in the result set it is passed
 * contains a prefix which already is displayed in the prefix list.
 */
function receivePrefixListUpdate(search_result, link_type) {

	pref_list = search_result.result;

	// Zero result elements. Should not happen as we at least always should
	// get the prefix we select to list, even if it has no children.
	if (pref_list.length == 0) {

		// TODO: Display notice dialog?
		log('Warning: no prefixes returned from list operation.');
		return true;

	// One result element (the prefix we searched for)
	} else if (pref_list.length == 1) {

		// remove expand button
		$("#prefix_indent" + pref_list[0].id).html('&nbsp;');
		prefix_list[pref_list[0].id].children = 0;
		return true;

	} else {

		// If the result set we received contains more elements, we assume at
		// least one of them is a child of the first element and set the number
		// of children to 1. This is (probably) not the correct value, but will
		// suffice for giving the right collapse behaviour.
		prefix_list[pref_list[0].id].children = 1;

	}

	insertPrefixList(pref_list);

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
		return;

	}

	insertPrefixList(pref_list);
	outstanding_nextpage = 0;

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
 * Insert a list of prefixes
 *
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
		showPrefix(prefix, $("#prefix_list"), null);
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

		prev_prefix = prefix;

	}

	// If the last prefix was added to a hidden container, unhide
	// if there are not very many prefixes in it
	var p_parent = $("#prefix_entry" + prev_prefix.id).parent();
	if (parseInt(p_parent.find('.prefix_entry').length) < 4) {
		unhide( p_parent.attr('data-prefix-id') );
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

	if (prefix.indent > prev_prefix.indent) {
		// Indent level incresed

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

		// We know (since we are one indent level below previous) that
		// it has at least one child.
		if (prev_prefix.children == -2) {
			prev_prefix.children = -1;
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

		/* Find the collapse container which the previous prefix was placed
		 * into. As it might be placed in a hidden container, we might need to
		 * go two steps down in the DOM tree.
		 */
		main_container = $("#prefix_entry" + prev_prefix.id).parent();
		if (main_container.hasClass('prefix_hidden_container')) {
			main_container = main_container.parent();
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
				// Main container last elemment, place hidden container after it.
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

			// does container already exist?
			var next = $("#prefix_entry" + prev_prefix.id).next();
			if (next.length == 0) {
				// create new if there is no next element or the next element is not a hidden container
				reference = addHiddenContainer(prefix, $("#prefix_entry" + prev_prefix.id), 'after');
				offset = null;
			} else {
				// there are elements after the previous one. Is it a collapse container?
				if (next.hasClass('prefix_hidden_container')) {
					reference = next;
					offset = 'prepend';
				} else {
					// next element was no collapse container. Add new before next element.
					reference = addHiddenContainer(prefix, next, 'before');
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

	// Determine if we need to fetch data
	if (prefix_list[id].children < 0) {

		// Yes, ask server for prefix list
		var data = {
			'schema': schema_id,
			'id': id,
			'include_parents': false,
			'include_children': false,
			'parents_depth': 0,
			'children_depth': 1,
			'max_result': 1000
		};
		$.getJSON("/xhr/search_prefix", data, receivePrefixListUpdate);

	} else {
		toggleGroup(id);
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

		$('#default_prefix_type').hide();
		$('#prefix_type_selection').show();

	}

	$('#radio-prefix-type-reservation').removeAttr('disabled');
	$('#radio-prefix-type-assignment').removeAttr('disabled');
	$('#radio-prefix-type-host').removeAttr('disabled');
	$('#radio-prefix-type-reservation').removeAttr('checked');
	$('#radio-prefix-type-assignment').removeAttr('checked');
	$('#radio-prefix-type-host').removeAttr('checked');

	// Re-evaluate node FQDN field when prefix length is changed. The same
	// thing for the prefix_length_prefix field is done in the selectPrefix
	// function. From some reason it can not be done here...
	$('input[name="prefix_length_pool"]').keyup(enableNodeFQDN);

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

	// enables/disables monitor and node FQDN options
	enableMonitor();
	enableNodeFQDN();

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
 * Function which determines whether the Node FQDN input element should
 * be enabled or not.
 */
function enableNodeFQDN() {

	/*
	 * Generally, the node fqdn option should only be available for host
	 * prefixes. However, there is one exception: loopbacks, which are defined
	 * as assignments with max prefix length.
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
		 * Enable if prefix length is max prefix length - not very easy to
		 * find!
		 *
		 * If we add a prefix from a pool, we have the length in an input
		 * field. Also the family can be fetched from an input field.
		 *
		 * If we add a prefix from another prefix, we can find the prefix
		 * length from the prefix length field and the family from the selected
		 * prefix
		 *
		 * If we add manually, we can extract the prefix from the prefix the
		 * user has typed in. But the family? Look for : in the prefix? :S
		 */

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

			// tricky case - enable
			$('input[name="prefix_node"]').removeAttr('disabled');

		} else {

			// not set - enable
			$('input[name="prefix_node"]').removeAttr('disabled');

		}

	 } else {

		// not set - enable
		$('input[name="prefix_node"]').removeAttr('disabled');

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

	enableNodeFQDN();

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
		$('#radio-prefix-type-reservation').attr('checked', true);
	} else if (cur_opts.pool.default_type == 'assignment') {
		$('#radio-prefix-type-assignment').attr('checked', true);
	} else if (cur_opts.pool.default_type == 'host') {
		$('#radio-prefix-type-host').attr('checked', true);
	}

	// show pool name and description
	$('#selected_pool_desc').html(pool_list[id].name + ' &mdash; ' + pool_list[id].description);
	if (pool_list[id].default_type != null) {
		$('#pool_prefix_type').html(pool_list[id].default_type);
		$('#default_prefix_type').show();
		$('#prefix_type_selection').hide();
	}

	// display data form
	$("#prefix_data_container").css('display', 'block');

	// set prefix length
	changeFamily();
	$('#length_info_row').css('display', 'block');
	$('#length_edit_row').css('display', 'inline-block');

	$("html,body").animate({ scrollTop: $("#length_info_row").offset().top - 50}, 700);
	$("#length_info_row").animate({ backgroundColor: "#ffffff" }, 1).delay(200).animate({ backgroundColor: "#dddd33" }, 300).delay(200).animate({ backgroundColor: "#ffffee" }, 1000);

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
		'schema': schema_id,
		'description': $('input[name="prefix_description"]').val(),
		'comment': $('textarea[name="prefix_comment"]').val(),
		'node': $('input[name="prefix_node"]').val(),
		'type': $('input[name="prefix_type"]:checked').val(),
		'country': $('input[name="prefix_country"]').val(),
		'order_id': $('input[name="prefix_order_id"]').val(),
		'vrf': $('input[name="prefix_vrf"]').val(),
		'alarm_priority': $('input[name="prefix_alarm_priority"]:checked').val(),
	};

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
		$('#length_info_text').html('<span class="tooltip" title="The parent prefix is of type assignment, prefix-length of the new prefix will thus be /' + maxpreflen + '.">/' + maxpreflen + '</span><input type="hidden" name="prefix_length_prefix" value=' + maxpreflen+ '>');
		$('.tooltip').tipTip({delay: 100});

		// enable / disable types
		$('#radio-prefix-type-reservation').attr('disabled', 'disabled');
		$('#radio-prefix-type-assignment').attr('disabled', 'disabled');
		$('#radio-prefix-type-host').removeAttr('disabled');

		$('#radio-prefix-type-host').attr('checked', 'checked');
	}

	// set prefix's pool attribute in NIPAP
	$('#prefix_data_container').show();
	$('#prefix_length_prefix_container').show();

	$('#alloc_from_prefix').html(prefix_list[prefix_id].prefix + ' &mdash; ' + prefix_list[prefix_id].description);
	cur_opts.from_prefix = prefix_list[prefix_id];

	$("html,body").animate({ scrollTop: $("#prefix_length_prefix_container").offset().top - 50}, 700);
	$("#prefix_length_prefix_container").animate({ backgroundColor: "#ffffff" }, 1).delay(200).animate({ backgroundColor: "#dddd33" }, 300).delay(200).animate({ backgroundColor: "#ffffee" }, 1000);

	// Enable keyup action on prefix length input field.
	// From some reason needs to be done here and not when the page is loaded,
	// where it is done for the prefix length field for pools.
	$('input[name="prefix_length_prefix"]').keyup(enableNodeFQDN);
	enableMonitor();

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
