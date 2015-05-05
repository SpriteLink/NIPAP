import cgi

from paste.urlparser import PkgResourcesParser
from webhelpers.html.builder import literal

from nipapwww.lib.base import BaseController
from nipapwww.controllers.xhr import XhrController

class ErrorController(BaseController):
    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    requires_auth = False

    def document(self):
        """Render the error document"""
        request = self._py_object.request
        resp = request.environ.get('pylons.original_response')
        content = literal(resp.body) or cgi.escape(request.GET.get('message', ''))

        page = """<!DOCTYPE html>
<html lang="en">
    <head>
        <title>NIPAP error</title>
        <meta charset="utf-8">
        <link rel="stylesheet" href="/nipap.css">
    </head>
    <body>
        <div class="top_menu">
            <div class="menu_entry" style="line-height: 0px">
                <div class="menu_entry" style="font-size: 10pt; color: #CCCCCC; padding-top: 11px; font-weight: bold;">
                NIPAP ERROR
                </div>
            </div>
        </div>
        <div class="content_outer">
            <div class="content_inner">
                <p>%s</p>
                <p>Relevant information has been forwarded to the system administrator.</p>
            </div>
			<div style="height: 500px;"> &nbsp; </div>
        </div>
    </body>
</html>""" % content

        # If the error was raised from the XhrController, return HTML-less response
        if type(request.environ['pylons.original_request'].environ.get('pylons.controller')) == XhrController:
            return content
        else:
            return page

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request = self._py_object.request
        request.environ['PATH_INFO'] = '/%s' % path
        return PkgResourcesParser('pylons', 'pylons')(request.environ, self.start_response)
