import cgi,os,sys,time
import types

from snakeserver.snakelet import Snakelet
from snakeserver.webform import FormUploadedFile, FormFileUploadError


class Snoop(Snakelet):

    # no special init method...

    def getDescription(self):
        return "request snooper"
    def requiresSession(self):
        return self.SESSION_DONTCREATE

    def serve(self, request, response):
        # don't set this, just take the default...: request.setEncoding("UTF-8")
        try:
            request.setMaxPOSTsize(self.getWebApp().getConfigItem("maxPOSTsize"))
            form = request.getForm()
        except FormFileUploadError,x:
            response.sendError(413,"upload too large")
            return
            
        out = response.getOutput()
        print >>out, '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
        print >>out, '<html><head><title>Request Snoop</title>'
        print >>out, '<style type="text/css">'
        print >>out, 'body { font-size: 10pt; font-family: sans-serif; color: black; background-color: #fffff8;}'
        print >>out, 'table { border: none;  border-collapse: collapse; }'
        print >>out, 'td,th { text-align: left; vertical-align: top; border: solid #e0d8d0 1px; margin: 0px; padding: 2pt; }'
        print >>out, 'th { border-bottom: solid #808080 1px; }'
        print >>out, 'span.listsep { color: #00a0a0; padding-left: 1ex; padding-right: 1ex; }'
        print >>out, '</style>'
        print >>out, '</head><body>'
        print >>out, '<h1>Request Snoop Snakelet</h1>'
        print >>out, '<p><a href="#form">Form params</a><span class="listsep">|</span>'
        print >>out, '<a href="#req">Request info</a><span class="listsep">|</span>'
        print >>out, '<a href="#headers">HTTP headers</a>'
        self.print_form(form,out)
        print >>out, '<h3><a name="req">Request parameters</a></h3>'
        print >>out, '<table>'
        print >>out, '<tr><th>Item</th><th>Value</th></tr>'
        print >>out, '<tr><td>Method</td><td>', self.escape(request.getMethod()),'</td></tr>'
        print >>out, '<tr><td>Full request URL</td><td>',self.escape(request.getRequestURL()),'</td></tr>'
        print >>out, '<tr><td>Plain request URL</td><td>',request.getRequestURLplain(),'</td></tr>'
        print >>out, '<tr><td>Full URL of the page</td><td>',self.getFullURL(),'</td></tr>'
        print >>out, '<tr><td>Full Query args</td><td>', self.escape(request.getFullQueryArgs()),'</td></tr>'
        print >>out, '<tr><td>Arg</td><td>', self.escape(request.getArg()),'</td></tr>'
        print >>out, '<tr><td>PathInfo</td><td>', self.escape(request.getPathInfo()),'</td></tr>'
        print >>out, '<tr><td>Query</td><td>', self.escape(request.getQuery()),'</td></tr>'
        print >>out, '<tr><td>urlpattern</td><td>',self.getURL(),'</td></tr>'
        print >>out, '<tr><td>Remote host</td><td>', self.escape(request.getRemoteHost()),'</td></tr>'
        print >>out, '<tr><td>Remote addr</td><td>', self.escape(request.getRemoteAddr()),'</td></tr>'
        print >>out, '<tr><td>Real Remote addr</td><td>', self.escape(request.getRealRemoteAddr()),'</td></tr>'
        print >>out, '<tr><td>Auth</td><td>', self.escape(request.getAuth()),'</td></tr>'
        print >>out, '<tr><td>Vhost</td><td>', self.getWebApp().getVirtualHost(),'</td></tr>'
        print >>out, '<tr><td>Server base URL</td><td>', request.getBaseURL(),'</td></tr>'
        session=request.getSession()
        if session:
            print >>out,"<tr><td>Session ID</td><td>",session.getID()+"</td></tr>"
            print >>out,"<tr><td>Session New?</td><td>",session.isNew(),"</td></tr>"
        else:
            print >>out,"<tr><td>Session</td><td>not present</td></tr>"
        print >>out, '</table>'

        print >>out, '<h3><a name="headers">All HTTP request headers</a></h3>'
        print >>out, '<table>'
        print >>out, '<tr><th>Header</th><th>Value</th></tr>'
        
        k=request.getAllHeaders().keys()
        k.sort()
        for h in k:
            hv=request.getHeader(h)
            print >>out,"<tr><td>",h,"</td><td>",self.escape(hv),"</td></tr>"
        print >>out, "</table>"
        print >>out,'</body></html>\n'

    def print_form(self, form,outs):
        """Dump the contents of a form as HTML."""
        keys = form.keys()
        keys.sort()
        print >>outs, '<h3><a name="form">Form Contents (form-POST or GET params)</a></h3>'
        if not keys:
            print >>outs, "<p><em>No form fields are present.</em>"
        else:
            print >>outs, '<table>'
            print >>outs, '<tr><th>Form field</th><th>Type</th><th>Value</th></tr>'
            for key in keys:
                print >>outs, "<tr><td>" + self.escape(key) + "</td><td>",
                value = form[key]
                if type(value) in types.StringTypes:
                    print >>outs,"str</td><td>",self.escape(value)
                elif type(value)==type([]):
                    print >>outs,"list</td><td>",'<span class="listsep"> | </span> '.join( [ self.escape(v) for v in value] )
                elif isinstance(value, FormUploadedFile):
                    print >>outs,"uploaded file</td><td>"
                    print >>outs, "<table>"
                    print >>outs, "<tr><td>filename</td><td>",value.filename,"</td></tr>"
                    print >>outs, "<tr><td>mimeType</td><td>",value.mimeType,"</td></tr>"
                    print >>outs, "<tr><td>typeOptions</td><td>",value.typeOptions,"</td></tr>"
                    print >>outs, "<tr><td>disposition</td><td>",value.disposition,"</td></tr>"
                    print >>outs, "<tr><td>disposition_options</td><td>",value.dispositionOptions,"</td></tr>"
                    contents=value.file.read(2000)
                    print >>outs,"<tr><td>content size</td><td>",len(contents)
                    if value.file.read(1):
                        truncated=True
                        print >>outs,"(truncated to 2000!!)"
                    else:
                        truncated=False
                    print >>outs, "</td></tr>"
                    if truncated:
                        print >>outs, "<tr><td>partial content</td><td>",
                    else:
                        print >>outs, "<tr><td>content</td><td>",
                    if value.mimeType.startswith("text/"):
                        print >>outs,"<pre>"+self.escape(contents)
                        if truncated:
                            print >>outs," &hellip;"
                        print >>outs,"</pre></td></tr>"
                    else:
                        print >>outs,"<em>not shown (binary data)</em></td></tr>"
                    print >>outs,"</table>"
                print >>outs,"</td></tr>"
            print >>outs, "</table>"

