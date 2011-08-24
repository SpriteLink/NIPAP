/**********************************************************************
 *
 * NAP JavaScript functions
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
var indent_head = Object();

// Object for storing statistics
var stats = Object();

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
			},
			modal: true,
			title: title,
			buttons: [
				{
					class: "button button_green",
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
function showDialogYesNo(title, msg, targetUrl) {
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
				$(this).parents(".ui-dialog:first").find(".button").removeClass("ui-state-default");
				$(this).parents(".ui-dialog:first").find(".button").removeClass("ui-state-focus");
			},
			modal: true,
			title: title,
			buttons: [
				{
					class: "button button_red",
					style: 'margin: 10px; width: 50px;',
					text: "Yes",
					click: function() { window.location.href = targetUrl; },
				},
				{
					class: "button button_green",
					style: 'margin: 10px; width: 50px;',
					text: "No",
					click: function() { $(this).dialog("close"); }
				}
			]
		});

	dialog.dialog('open');

	return false;
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

	displayNotice('Server error', thrownError);

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
	exp.html('-');

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
		$('#prefix_list').empty();
		$('#search_interpret_container').empty();
		$('#search_result_help').show();
		$('#nextpage').hide();
		query_id += 1;
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

}

/*
 * Called when next page of results is requested by the user.
 */
function performPrefixNextPage () {
	if (outstanding_nextpage == 1 || end_of_result == 1) {
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
 */
function showPrefix(prefix, parent_container) {

	// add main prefix container
	parent_container.append('<div id="prefix_entry' + prefix.id + '">');
	var prefix_entry = $('#prefix_entry' + prefix.id);
	prefix_entry.addClass('prefix_entry');
	prefix_entry.append('<div id="prefix_row' + prefix.id + '">');
	var prefix_row = $('#prefix_row' + prefix.id );
	if (prefix.match == true) {
		prefix_row.addClass("row_match");
	} else {
		prefix_row.addClass("row_collateral");
	}
	prefix_row.hover(
		function() { prefix_row.addClass("row_hover"); },
		function() { prefix_row.removeClass("row_hover"); }
	);

	// add indent and prefix container
	prefix_row.append('<div id="prefix_ind_pref' + prefix.id + '">');
	var prefix_ind_pref = $('#prefix_ind_pref' + prefix.id);
	prefix_ind_pref.addClass('prefix_column');
	prefix_ind_pref.addClass('prefix_ind_pref');

	// add indent
	prefix_ind_pref.append('<div id="prefix_indent' + prefix.id + '">');
	var prefix_indent = $('#prefix_indent' + prefix.id);
	prefix_indent.addClass("prefix_indent");

	// If the prefixes has children  (or we do not know), add expand button
	if (prefix.children == 0 || hasMaxPreflen(prefix)) {

		// the prefix_indent container must contain _something_
		prefix_indent.html('&nbsp;');

	} else {

		// add expand button
		prefix_indent.html('<span class="prefix_exp" id="prefix_exp' + prefix.id + '" onClick="collapseClick(' + prefix.id + ')">+</span>');

		// If we are sure that the children has been fetched, the group will
		// already be fully expanded and a minus sign should be shown
		if (prefix.children == 1) {
			$("#prefix_exp" + prefix.id).html("-");
		}

	}

	prefix_indent.width(prefix_indent.width() + 30 * prefix.indent);

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

	// add button
	prefix_row.append('<div id="prefix_button_col' + prefix.id + '">')
	var prefix_button_col = $('#prefix_button_col' + prefix.id);
	prefix_button_col.addClass('prefix_column');
	prefix_button_col.addClass('prefix_button_col');
	prefix_button_col.append('<div id="prefix_button' + prefix.id + '" data-prefix-id="' + prefix.id + '">');

	var prefix_button = $('#prefix_button' + prefix.id);
	prefix_button.addClass('minibutton');
	prefix_button.addClass('prefix_button');
	prefix_button.html("<div class='prefix_button_icon' class='prefix_button_icon'>&nbsp;</span>");
	prefix_button.click(prefix, function(e) { showPrefixMenu(e.currentTarget.getAttribute('data-prefix-id')); e.preventDefault(); });

	// Add prefix menu
	prefix_row.append('<div id="prefix_menu' + prefix.id + '">');
	var prefix_menu = $('#prefix_menu' + prefix.id);
	prefix_menu.addClass("prefix_menu");
	prefix_menu.html("<h3>Prefix menu</h3>");

	// Add different manu entries depending on where the prefix list is displayed
	if (prefix_link_type == 'select') {
        // select prefix (allocate from prefix function on add prefix page)
	} else if (prefix_link_type == 'add_to_pool') {
        // Add to pool (Add prefix to pool on edit pool page)
	} else {
		// ordinary prefix list
		prefix_menu.append('<a href="/prefix/edit/' + prefix.id + '?schema=' + schema_id + '">Edit</a>');
		prefix_menu.append('<a href="/prefix/remove/' + prefix.id + '?schema=' + schema_id + '">Remove</a>');
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
	prefix_row.append('<div id="prefix_span_order' + prefix.id + '">');
	var prefix_span_order = $('#prefix_span_order' + prefix.id);
	prefix_span_order.addClass('prefix_column');
	prefix_span_order.addClass('prefix_span_order');
	if (prefix.span_order == null || prefix.span_order == '') {
		prefix_span_order.html("&nbsp;");
	} else {
		prefix_span_order.html(prefix.span_order);
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

}

/*
 * Show the prefix menu
 */
function showPrefixMenu(prefix_id) {

	// find menu
	var menu = $('#prefix_menu' + prefix_id);

	// show overlay
	$(".prefix_menu_overlay").show();

	// Set menu position
	var button_pos = $('#prefix_button' + prefix_id).position();
	menu.css('top', button_pos.top + $('#prefix_button' + prefix_id).height() + 5 + 'px');
	menu.css('left', button_pos.left + 'px');
	menu.slideDown('fast');

}


/*
 * Callback function called when prefixes are received.
 * Plots prefixes and adds them to list.
 */
function receivePrefixList(search_result) {
	stats.response_received = new Date().getTime();

	if (! ('query_id' in search_result.search_options)) {
		displayNotice("Error", 'No query_id');
		return;
	}
	if (parseInt(search_result.search_options.query_id) < parseInt(newest_query)) {
		return;
	}
	newest_query = parseInt(search_result.search_options.query_id);

	// Error?
	if ('error' in search_result) {
		displayNotice("Error", search_result.message);
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

			if ('strict_prefix' in interp) {
				text += '<b>' + interp.strict_prefix + '</b>';
				tooltip = 'Prefix must be contained within ' + interp.strict_prefix + ', which is the base prefix of ' + interp.expanded + ' (automatically expanded from ' + interp.string + ')';
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
			tooltip = "The description OR node OR the comment should regexp match '" + interp.string + "'";
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

	if (search_result.prefix_list.length > 0) {

		// insert prefix list
		insertPrefixList(search_result.prefix_list, $("#prefix_list"), search_result.prefix_list[0]);

	} else {

		// No prefixes received
		$('#prefix_list').html('No prefixes found.');

	}

	stats.finished = new Date().getTime();

	// Display search statistics
	log('Rendering took ' + (stats.finished - stats.response_received) + ' milliseconds');
	$('#search_stats').html('Query took ' + (stats.response_received - stats.query_sent)/1000 + ' seconds.');

	// less than max_result means we reached the end of the result set
	if (search_result.prefix_list.length < search_result.search_options.max_result) {
		end_of_result = 1;
		$('#nextpage').hide();
	} else {
		$('#nextpage').show();
	}
}


/*
 * Receive an updated prefix list
 */
function receivePrefixListUpdate(search_result, link_type) {
	pref_list = search_result.prefix_list;

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

	}

	if (prefix_list[pref_list[0].id].type == 'reservation') {
		prefix_list[pref_list[0].id].children = -1;
	}
	insertPrefixList(pref_list.slice(1), $("#collapse" + pref_list[0].id), pref_list[0], link_type);

}


/*
 * Receive the "next page" of a prefix list
 */
function receivePrefixListNextPage(search_result) {
	pref_list = search_result.prefix_list;

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

	insertPrefixList(pref_list.slice(1), indent_head[pref_list[1].indent], pref_list[0]);

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
 * Insert prefixes into the list
 */
function insertPrefixList(pref_list, start_container, prev_prefix) {

	// return if we did not get any prefixes
	if (pref_list.length == 0) {
		return;
	}

	indent_head[pref_list[0].indent] = start_container;

	container = start_container;;
	// go through received prefixes
	for (key in pref_list) {

		prefix = pref_list[key];
		prefix_list[prefix.id] = prefix;

		// if there is no indent container for the current level, set
		// indent head for current indent level to the top level container
		if (!(prefix.indent in indent_head)) {
			indent_head[prefix.indent] = $('#prefix_list');
			log("Adding element to top level group");
		}

		// Has indent level increased?
		if (prefix.indent > prev_prefix.indent) {
			// we get the number of children for assignments from the database
			if (prev_prefix.type == 'assignment') {
				// if previous assignment was a match, we don't need to expand
				if (prev_prefix.match != 1) {
					expandGroup(prev_prefix.id);
				}
			} else {
				if (prev_prefix.children == -2) {
					// but for reservations we can set it to -1, ie at least
					// one if we don't already have all the children, in case
					// we just expand
					prev_prefix.children = -1;
				}
				expandGroup(prev_prefix.id);
			}
			container = indent_head[prefix.indent];
		}
		if (prefix.type == 'host' && prev_prefix.indent < prefix.indent && prefix.match == false) {
			container.append('<div id="prefix_hidden_container' + prefix.id + '" class="prefix_hidden_container"></div>');
			container.append('<a id="prefix_hidden_text' + prefix.id + '" class="prefix_hidden_text" href="javascript:void(0);" onclick="unhide(' + prefix.id + ');">(hidden prefixes, click to display)</a>');
			container = $('#prefix_hidden_container' + prefix.id);
		}
		if (prev_prefix.indent == prefix.indent) {
		   if (prev_prefix.match == false && prefix.match == true) {
			   // switching into a match from a non-match, so we should display a "expand upwards" arrow
			   container = indent_head[prefix.indent];
		   } else if (prev_prefix.match == true && prefix.match == false) {
				// switching into a non-match from a match, so we should display a "expand downwards" arrow
				container.append('<div id="prefix_hidden_container' + prefix.id + '" class="prefix_hidden_container"></div>');
				container.append('<a id="prefix_hidden_text' + prefix.id + '" class="prefix_hidden_text" onclick="unhide(' + prefix.id + ');">(hidden prefixes, click to display)</a>');
				container = $('#prefix_hidden_container' + prefix.id);
		   }
		}

		prev_prefix = prefix;

		// Only display prefixes we are supposed to display
		if (prefix.display != true) {
			continue;
		}

		showPrefix(prefix, container);

		// add collapse container for current prefix
		if (!hasMaxPreflen(prefix)) {
			indent_head[prefix.indent].append('<div class="prefix_collapse" id="collapse' + prefix.id + '">');
			indent_head[prefix.indent + 1] = $('#collapse' + prefix.id);
		}

	}

}

/*
 * Function which is run when a collapse +/- sign is clicked.
 */
function collapseClick(id) {

	// Determine if we need to fetch data
	if (prefix_list[id].children == -2) {

		// Yes, ask server for prefix list
		var data = {
			'schema': schema_id,
			'id': id,
			'include_parents': false,
			'include_children': false,
			'parents_depth': 0,
			'children_depth': 1
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
	log("Unhide called for " + id);
	$('#prefix_hidden_container' + id).show();
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

	}

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
 * Is run when the adress family is changed
 */
function changeFamily() {

	// set prefix length in pool length input
	if (alloc_method == 'from-pool') {

		$('input[name="prefix_length_pool"]').val(cur_opts.pool.length_v4);

		if ($('input[name="prefix_family"]:checked').val() == '4') {
			$('input[name="prefix_length_pool"]').val(cur_opts.pool.length_v4);
			$('#def_length_container').html("Use pool's default IPv4 prefix-length of /" + cur_opts.pool.length_v4 + ".");
		} else {
			$('input[name="prefix_length_pool"]').val(cur_opts.pool.length_v6);
			$('#def_length_container').html("Use pool's default IPv6 prefix-length of /" + cur_opts.pool.length_v6 + ".");
		}
	}

	// TODO: set prefix length in prefix input

}


/*
 * Run when a pool is selected from the pool list.
 */
function selectPool(e, ui) {

	// Save the pool
	cur_opts.pool = ui.item;

	// display data form
	$("#prefix_data_container").css('display', 'block');

	// set prefix length
	changeFamily();
	$('#length_info_row').css('display', 'block');
	$('#length_edit_row').css('display', 'inline-block');

}


/*
 * Enable from-pool autocompleting search box.
 */
function enableFromPoolSearch(data) {

	var pools = new Array();

	for (p in data) {
		pools.push({
			'value': data[p].name,
			'id': data[p].id,
			'length_v4': data[p].ipv4_default_prefix_length,
			'length_v6': data[p].ipv6_default_prefix_length
			});
	}

	$("#from-pool").autocomplete({
		'source': pools,
		'select': selectPool
	});

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
		'span_order': $('input[name="prefix_span_order"]').val(),
		'alarm_priority': $('input[name="prefix_alarm_priority"]:checked').val(),
		'monitor': $('input[name="prefix_monitor"]').val(),
	};

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

		prefix_data.from_prefix = cur_opts.from_prefix;
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
	} else if (prefix_list[prefix_id].type == 'assignment') {
		$('#length_info_text').html('<span class="tooltip" title="The parent prefix is of type assignment, prefix-length of the new prefix will thus be /32.">/32</span>');
		$('.tooltip').tipTip({delay: 100});
	}

	// set prefix's pool attribute in Nap
	$('#prefix_data_container').show();
	$('#prefix_length_prefix_container').show();

	$('#alloc_from_prefix').html(prefix_list[prefix_id].prefix + ' &mdash; ' + prefix_list[prefix_id].description);
	cur_opts.from_prefix = new Array(prefix_list[prefix_id].prefix);

	$("html,body").animate({ scrollTop: $("#prefix_length_prefix_container").offset().top - 50}, 700);
	$("#prefix_length_prefix_bg").animate({ backgroundColor: "#ffffff" }, 1).delay(200).animate({ backgroundColor: "#dddd33" }, 300).delay(200).animate({ backgroundColor: "#ffffee" }, 1000);

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
