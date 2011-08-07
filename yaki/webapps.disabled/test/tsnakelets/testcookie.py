import cgi,os,sys

from snakeserver.snakelet import Snakelet
import Cookie

class TestCookie(Snakelet):

    def requiresSession(self):
        return self.SESSION_NOT_NEEDED

    def serve(self, request, response):
        if request.getArg()!='check':
            # serve a cookie to the second stage (?check)
            # to check if cookies are enabled.
            response.setCookie("test","test-value")
            response.HTTPredirect(self.getURL()+"?check")
        else:
            out = response.getOutput()
            cookies=Cookie.SimpleCookie(request.getCookie())
            print >>out, '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
            
            if not cookies.has_key("test"):
                # cookies are disabled!
                print >>out, """<html><head><title>Cookies disabled</title></head><body><h2>Cookies not enabled</h2>
<p>You have disabled cookies in your browser (at least for this site).
The site requires cookies to be enabled to work correctly.
<p><strong>Why cookies?</strong> The cookie is used to store your user identification,
so we know who you are. The cookie is removed when you exit the browser.
<em>No</em> personal information (password, user name) is stored in the cookie, only a unique identifier that
we generate for you and use internally.
<p><strong>Solution:</strong> Please enable cookies for this site and <a href="%s">try again.</a>
<p><address>This is an example text. The cookie-test has been done by a Snakelet.</address>
</body></html>""" % self.getURL()
                return

            # we got the test cookie back, so cookies are enabled!
            print >>out, """<html><head><title>Cookies enabled</title></head><body><h2>Cookies enabled</h2>
<p>You have enabled cookies in your browser (at least for this site).
You can now proceed with the login procedure... etc.. etc..
<p>Try to disable cookies now and refresh the page...
<p><address>This is an example text. The cookie-test has been done by a Snakelet.</address>
</body></html>"""

