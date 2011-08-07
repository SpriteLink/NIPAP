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
 * attribute: has_children. It is used to save information regarding
 * whether the prefix has children or not. These values are allowed:
 *  -2: We have no clue
 *  -1: At least one, but might be more (used for parent prefixes which
 *	  was received when a prefix further down was requested including
 *	  parents)
 *   0: No children
 *   1: Has children
 */
var prefix_list = Object();
var indent_head = Object();

/*
 * Holy shit, this is an ugly hack...
 * As the prefix search results sometimes need to link to an edit-prefix-page
 * and sometimes need to link to a select-prefix function, we keep the current
 * state in a global variable...
 */
var prefix_link_type = 'edit';

// Max prefix lengths for different address families
var max_prefix_length = [32, 128];


/**
 * Display a notice popup
 *
 * @param title string Title to display above error message.
 * @param msg Message to display to user.
 */
function displayNotice(title, msg) {

	// Don't display more than one popup
	if ($("#notice_dialog").length) {
		return;
	}

	$("body").append('<div class="fade_bg">');
	$("body").append('<div id="notice_dialog" class="dialog">');
	$("#notice_dialog").html('<h3 class="dialog_title">' + title + '</h3>' +
		'<div class="dialog_text">' + msg + "</div>" +
		'<div class="dialog_options">' +
		'<div class="button button_green" id="close_notice_btn">' +
		'<div style="display: inline-block; vertical-align: middle;">OK</div>' +
		'</div>');
	$("#close_notice_btn").click(removeNotice);

	$(".fade_bg").fadeIn(200);
	$("#notice_dialog").fadeIn(200);

}

/*
 * Remove notice popup.
 */
function removeNotice() {
	
	$("#notice_dialog").fadeOut(200);
	$(".fade_bg").fadeOut(200);
	window.setTimeout(function() { $("#notice_dialog").remove(); }, 200);
	window.setTimeout(function() { $(".fade_bg").remove(); }, 200);

}

/*
 * Display verification dialog.
 * TODO: remove inline javascript on no-option
 * TODO: add support for passing javascript functions instead of URLs
 */
function displayVerify(msg, url) {

	$('body').append('<div class="fade_bg">');
	$('body').append('<div class="dialog" id="verify_dialog">');
	var d = $('#verify_dialog');
	d.append('<h3 class="dialog_title">Are you sure?</h3>');
	d.append('<div class="dialog_text">' + msg + '</div>');
	d.append('<div class="dialog_options">' +
	'<a href="' + url + '"><div class="button button_green" style="margin: 10px;">' +
	'<div style="display: inline-block; vertical-align: middle;">YES</div></div></a>' +
	'<a href="javascript:void(0);" onclick="removeVerify();">' +
	'<div class="button button_red" style="margin: 10px;">' +
	'<div style="display: inline-block; vertical-align: middle;">NO</div></div></a>');

	$(".fade_bg").fadeIn(200);
	$("#verify_dialog").fadeIn(200);

	return false;
	
}

/*
 * Remove verification dialog
 */
function removeVerify() {

	$("#verify_dialog").fadeOut(200);
	$(".fade_bg").fadeOut(200);
	window.setTimeout(function() { $("#verify_dialog").remove(); }, 200);
	window.setTimeout(function() { $(".fade_bg").remove(); }, 200);

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
	exp.html('&nbsp;-&nbsp;');

}

/*
 * Collapse a collapse group
 */
function collapseGroup(id) {

	var col = $('#collapse' + id);
	var exp = $('#prefix_exp' + id);

	col.slideUp();
	exp.html('&nbsp;+&nbsp;');

}

/*
 * Perform a search operation
 */
function performPrefixSearch() {

	// Skip search if query string empty
	if (jQuery.trim($('#query_string').val()).length < 1) {
		return true;
	}

	var search_q = {
		'query_string': $('#query_string').val(),
		'schema': schema_id,
		'parents_depth': optToDepth($('input[name="search_opt_parent"]:checked').val()),
		'children_depth': optToDepth($('input[name="search_opt_child"]:checked').val()),
		'include_all_parents': 'true',
		'include_all_children': 'false',
		'max_result': 50,
		'offset': 0
	}

	$.getJSON("/xhr/smart_search_prefix", search_q, receivePrefixList);

}


/*
 * Add a prefix to the prefix list.
 */
function showPrefix(prefix, parent_container) {

	// add main prefix container
	parent_container.append('<div id="prefix_entry' + prefix.id + '">');
	var prefix_entry = $('#prefix_entry' + prefix.id);
	prefix_entry.attr('class', 'prefix_entry');
	prefix_entry.hover(
		function() { prefix_entry.addClass("row_hover"); },
		function() { prefix_entry.removeClass("row_hover"); }
	);

	// add indent and prefix container
	prefix_entry.append('<div id="prefix_ind_pref' + prefix.id + '">');
	var prefix_ind_pref = $('#prefix_ind_pref' + prefix.id);
	prefix_ind_pref.addClass('prefix_ind_pref');

	// add indent
	prefix_ind_pref.append('<div id="prefix_indent' + prefix.id + '">');
	var prefix_indent = $('#prefix_indent' + prefix.id);
	prefix_indent.addClass("prefix_indent");

	// If the prefixes has children  (or we do not know), add expand button
	if (prefix.has_children == 0 || hasMaxPreflen(prefix)) {

		// the prefix_indent container must contain _something_
		prefix_indent.html('&nbsp;');

	} else {

		// add expand button
		prefix_indent.html('<span class="exp_button" id="prefix_exp' + prefix.id + '" onClick="collapseClick(' + prefix.id + ')">&nbsp;+&nbsp;</span>');

		// If we are sure that the children has been fetched, the group will
		// already be fully expanded and a minus sign should be shown
		if (prefix.has_children == 1) {
			$("#prefix_exp" + prefix.id).html("&mbsp;-&nbsp;");
		}

	}

	prefix_indent.width(prefix_indent.width() + 30 * prefix.indent);

	// add prefix
	prefix_ind_pref.append('<div id="prefix_prefix' + prefix.id + '">');
	var prefix_prefix = $('#prefix_prefix' + prefix.id);
	prefix_prefix.addClass("prefix_prefix");
	if (prefix_link_type == 'select') {
		prefix_prefix.html('<a href="javascript:void(0);" onClick="selectPrefix(' + prefix.id + '); return false;">' + prefix.display_prefix + '</a>');
	} else if (prefix_link_type == 'add_too_pool') {
		prefix_prefix.html('<a href="/pool/add_prefix/' + pool_id + '?prefix=' + prefix.id + '&schema=' + schema_id + '" onClick="selectPrefix(' + prefix.id + '); return false;">' + prefix.display_prefix + '</a>');
	} else {
		prefix_prefix.html('<a href="/prefix/edit/' + prefix.id + '?schema=' + schema_id + '">' + prefix.display_prefix + '</a>');
	}

	// Add prefix type
	prefix_entry.append('<div id="prefix_type' + prefix.id + '">');
	var prefix_type = $('#prefix_type' + prefix.id);
	prefix_type.addClass("prefix_type");
	prefix_type.html(prefix.type);

	// Add prefix description
	prefix_entry.append('<div id="prefix_description' + prefix.id + '">');
	var prefix_description = $('#prefix_description' + prefix.id);
	prefix_description.addClass("prefix_description");
	prefix_description.html(prefix.description);

}


/*
 * Callback function called when prefixes are received.
 * Plots prefixes and adds them to list.
 */
function receivePrefixList(pref_list) {

	// Error?
	if ('error' in pref_list) {
		displayNotice("Error", pref_list.message);
		return;
	}

	/*
	 * Interpretation list
	 */
	var intp_cont = $("#search_interpret_container");
	intp_cont.empty();
	for (key in pref_list.interpretation) {

		var interp = pref_list.interpretation[key];
		intp_cont.append('<div class="search_interpretation" id="intp' + key + '">');
		var text = '<b>' + interp.string + '</b> interpreted as ' + interp.interpretation;
		if ('expanded' in interp) {
			text = text + ' (<b>' + interp.expanded + '</b>)';
		}
		$('#intp' + key).html(text);

	}

	/*
	 * Prefix list
	 */
	// clean up old stuff
	$('#prefix_list').empty();
	prefix_list = new Object();
	indent_head = new Object();

	// insert prefix list
	insertPrefixList(pref_list.result, $("#prefix_list"), pref_list.result[0]);

}


/*
 * Receive an updated prefix list
 */
function receivePrefixListUpdate(pref_list, link_type) {

	// handle different return data from search and smart_search
	if ('result' in pref_list) {
		pref_list = pref_list.result;
	}

	// Zero result elements. Should not happen as we at least always should
	// get the prefix we select to list, even if it has no children.
	if (pref_list.length == 0) {

		// TODO: Display notice dialog?
		console.log('Warning: no prefixes returned from list operation.');
		return true;

	// One result element (the prefix we searched for)
	} else if (pref_list.length == 1) {

		// remove expand button
		$("#prefix_indent" + pref_list[0].id).html('&nbsp;');
		prefix_list[pref_list[0].id].has_children = 0;
		return true;

	}

	prefix_list[pref_list[0].id].has_children = 1;
	insertPrefixList(pref_list.slice(1), $("#collapse" + pref_list[0].id), pref_list[0], link_type);

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
		console.log("insertPrefixList: No prefixes received");
		return;
	}

	indent_head[pref_list[0].indent] = start_container;

	// go through received prefixes
	for (key in pref_list) {

		prefix = pref_list[key];
		prefix_list[prefix.id] = prefix;

		// a host has no children, otherwise we do not know
		if (prefix.type == 'host') {
			prefix.has_children = 0;
		} else {
			prefix.has_children = -2;
		}

		// if there is no indent container for the current level, set
		// indent head for current indent level to the top level container
		if (!(prefix.indent in indent_head)) {
			indent_head[prefix.indent] = $('#prefix_list');
			console.log("Adding element to top level group");
		}

		// Has indent level increased?
		if (prefix.indent > prev_prefix.indent) {

			expandGroup(prev_prefix.id);
			prev_prefix.has_children = -1;
		}

		prev_prefix = prefix;

		// Only display prefixes we are supposed to display
		if (prefix.display != true) {
			continue;
		}

		showPrefix(prefix, indent_head[prefix.indent]);

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
	if (prefix_list[id].has_children == -2) {

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
		$("#prefix_row").hide();
		$("html,body").animate({ scrollTop: $("#from-prefix_container").offset().top - 50}, 700);

	// from-pool
	} else if (e.currentTarget.id == 'radio-from-pool') {

		alloc_method = 'from-pool';

		$("#from-prefix_container").hide();
		$("#from-pool_container").show();
		$("#prefix_data_container").hide();
		$("#prefix_row").hide();
		$('#prefix_length_prefix_container').hide();
		$("html,body").animate({ scrollTop: $("#from-pool_container").offset().top - 50}, 700);

	// else - manual
	} else {

		alloc_method = 'manual';

		$("#from-prefix_container").hide();
		$("#from-pool_container").hide();
		$("#prefix_data_container").show();
		$("#prefix_row").css('display', 'table-row');
		$('#prefix_length_prefix_container').hide();
		$("html,body").animate({ scrollTop: $("#prefix_data_container").offset().top - 50}, 700);

	}

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
