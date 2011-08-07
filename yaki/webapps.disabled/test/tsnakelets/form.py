import cgi,os,sys,time

from snakeserver.snakelet import Snakelet
from snakeserver.webform import FormUploadedFile, FormFileUploadError


# this one reads the form post using iso-8859-15 encoding
class FormAccepter(Snakelet):

    def requiresSession(self):
        return self.SESSION_NOT_NEEDED

    def setInputEncoding(self, request):
        request.setEncoding("iso-8859-15")

    def serve(self, request, response):
        self.setInputEncoding(request)
        
        form = request.getForm()
        
        requiredEnc = request.getParameter("outputencoding");
        text = request.getParameter("text")
        
        if not requiredEnc:
            requiredEnc = sys.getdefaultencoding()

        response.setContentType("text/html")
        response.setEncoding(requiredEnc)

        out = response.getOutput()
        print >>out,'<html><body>'
        print >>out, "<h2>Form results</h2>"
        print >>out, "<h3>Request parameters:</h3><p>"
        print >>out, "Content type=", self.escape(request.getContentType()),"<br>"
        print >>out, "Content length=", request.getContentLength(),"<br>"
        print >>out, "Request char enc=", request.getEncoding(),"<br>"
        print >>out, "Default encoding="+sys.getdefaultencoding(),"<br>"
        print >>out, "Out encoding="+requiredEnc,"<br>"
        print >>out, "<h3>Submitted text:</h3><p>"

        if text:
            print >>out, "<p>TEXT={"+text+"}    length=",len(text),"   type=",self.escape(repr(type(text)))
            print >>out, "<br>TEXT BYTES: { "
            for c in text:
                print >>out, hex(ord(c)), " "
            print >>out, " }<br>"
        else:
            print >>out, "<p>NO TEXT!!<br>"
            
        print >>out, "<p>"
        if type(text) is unicode:
            print >>out,"&#x2713; type of text is unicode.<br>"
        else:
            print >>out,"&#x2717; <em>type of text is not unicode!</em><br>"
        if len(text)==4:
            print >>out,"&#x2713; text consists of 4 characters.<br>"
        else:
            print >>out,"&#x2717; <em>text does not consist of 4 characters!</em><br>"
        if text==u'\u20ac\u00eb\u00a9\u2661':
            print >>out,"&#x2713; text contains the correct unicode characters.<br>"
        else:
            print >>out,"&#x2717; <em>text does not contain the correct unicode characters!</em><br>"
            
        print >>out,"<hr>"
        print >>out,"""<p><strong>This is what you <em>should</em> see:</strong>
<p>TEXT={&euro;&euml;&copy;&#x2661;} length= 4 type= &lt;type 'unicode'&gt;
<br>TEXT BYTES: { 0x20ac 0xeb 0xa9 0x2661 } </p>"""
        print >>out,'</body></html>\n'


# this one reads the form post using UTF-8 encoding
class UTF8FormAccepter(FormAccepter):

    def setInputEncoding(self, request):
        request.setEncoding("UTF-8")
