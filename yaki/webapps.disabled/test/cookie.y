<%@session=yes%>
<%
checkArg="_cookiecheck_"
if self.Request.getSession().isNew() and self.Request.getArg()!=checkArg:
    # Session is new, so do the cookie check.
    # (force a page reload-- this way we will see if our cookie comes back)
    self.Yhttpredirect(self.getURL()+'?'+checkArg)

if self.Request.getSession().isNew():
    # If, after the http redirect, the session is again NEW, the
    # browser is not sending session cookies.
    self.write("<html><body>")
    self.write("<p>You have disabled session cookies for this website.")
    self.write("<br>Enable cookies, then <a href=\""+self.getURL()+"\">try again</a>.")
    self.write("</body></html>")
    return
    # ... you could also redirect to error page
elif self.Request.getArg()==checkArg:
    # Session is not NEW, so cookies are okay; redirect back to the 'normal' url.
    # This is not strictly needed, but it looks nicer in the browser.
    self.Yhttpredirect(self.getURL())
%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Cookies ok</title></head>
<body>
<p>Your browser accepted the session cookie.  Everything is fine :-)</p>
<p>Try disabling cookies now, and reload this page...</p>
</body>
</html>
