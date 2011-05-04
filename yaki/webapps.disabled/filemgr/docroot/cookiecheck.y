<%!--=========================================

    Logic to check if session cookies are
    enabled. Also contains the error page.

============================================--%>
<%@pagetemplate=TEMPLATE.y%>
<%@session=no%>
<%

# This method uses redirection to itself to check if
# the session cookie is accepted by the browser.

def checkCookies():
    checkArg="_cookiecheck_"
    if not self.Request.getSession():
        self.abort("page has no session at all")
    if self.Request.getSession().isNew() and self.Request.getArg()!=checkArg:
        self.Yhttpredirect(self.getURL()+'?'+checkArg)
    
    cookies=True
    if self.Request.getSession().isNew():
        toErrorPage()
    elif self.Request.getArg()==checkArg:
        self.Yhttpredirect(self.getURL())

def toErrorPage():
    self.Request.setArg("error")
    if not self.Request.getParameter("returnpage"):
        self.Request.getForm()["returnpage"]=self.URLprefix
    self.Yredirect("cookiecheck.y")

%>
<%if self.Request.getArg()=="error":%>
<div class="contentcolumn">
<h4>Cookies are disabled in your browser</h4>
<p>The page you requested, needs session cookies to be enabled for this website.</p>
<p>Please enable them, and <a href="<%=self.escape(self.Request.getParameter("returnpage"))%>">try again</a>.</p>
<p>&nbsp;</p>
<p><span class="light"><strong>Why cookies?</strong> The cookie is used to store your user identification,
so we know who you are, and that we can relate your browser requests to a single session.
 The cookie is removed when you exit the browser.
<em>No</em> personal information (password, user name) is stored in the cookie, only a unique identifier that
we generate for you and use internally.</span>
</p>
</div>
<%end%>
