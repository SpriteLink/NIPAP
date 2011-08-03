/**********************************************************************
 *
 * NAP JavaScript functions
 *
 *********************************************************************/

/**
 * Global variables...
 */


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
