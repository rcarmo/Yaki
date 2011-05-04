<%!--============================================
    LOGIN page.
================================================--%>
<%@inputencoding="ISO-8859-1"%>
<%@pagetemplate=TEMPLATE.y%>
<%@inherit=snakeserver.user.LoginPage%>
<%$include="cookiecheck.y"%>
<%

self.Request.setEncoding("UTF-8")    

if not self.Request.getParameter("src")=="frog":
    # check cookies (only if not linked from Frog)
    checkCookies()

if self.User or self.Request.getArg()=="logout":
    self.Request.getSession().logoutUser()
    self.User=None
    self.Request.setArg(None)
    self.SessionCtx.from_other=False
    self.Yredirect(self.getURL())

# use the standard Snakelets login-page mechanism
self.attemptLogin( "index.y" ) 

# If the login succeeded, we are forwarded to the target page.
# If we're still here, the login failed..
error=''
if self.Request.getParameter("login"):
    error="Invalid login"


# Frog integration (or another webapp) -- also see index.y; it contains the same logic
o_src=self.Request.getParameter("src")
o_user=self.Request.getParameter("user")
o_returnurl=self.Request.getParameter("returnurl")
if o_src and o_user and o_returnurl:
    user=o_user
    self.RequestCtx.login=user
    self.SessionCtx.from_other=True
    self.SessionCtx.filemgr_return_url=o_returnurl
else:
    if not hasattr(self.SessionCtx,"from_other"):
        self.SessionCtx.from_other=False

%>

<%!--=========================== LOGIN FORM ===================--%>
<div class="contentcolumn">
<br />
<h4>Log in to access your files</h4>
<%
frogAuth=None
try:
    sharedauth=self.getPlugin("SharedAuth")
    frogAuth=sharedauth.webappMapping[self.WebApp.getName()[0]]   # XXX hack-ish to obtain the other webapp
except KeyError:
    pass
if frogAuth:
    self.write("<h5>Use the same account as you use in %s.</h5>" % frogAuth.getName()[0].capitalize())
%>
<form action="<%=self.getURL()%>" method="post" accept-charset="UTF-8">
<table border="0" cellspacing="10" cellpadding="1" summary="Login form">
  <tr>
    <td align="right">Name</td>
    <td>
      <input type="text" name="login" value="<%=self.Request.getParameter("login")%>" />
    </td>
  </tr>
  <tr>
    <td align="right">Password</td>
    <td><input type="password" size="21" maxlength="20" name="password" /></td>
  </tr>
  <tr>
    <td />
    <td><input type="submit" value="Log in" /></td>
  </tr>
  <tr>
    <td />
    <td><strong><%=error%></strong>&nbsp;</td>
  </tr>
</table>
</form>
</div>
