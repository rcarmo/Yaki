<%@session=yes%>
<%@inherit=snakeserver.user.LoginPage%>
<%

# first, check if we have to log out.
if self.Request.getParameter("logout"):
    self.Request.deleteSession()
    self.User=None
else:
    self.attemptLogin("serverinfo")       # call the base class, to attempt to log in 

# if we get here, the login failed.. (or we just logged out)
error=''
if self.Request.getParameter("login"):
    error="Invalid login"

%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><title>WebApp management login</title><link rel="stylesheet" type="text/css" href="manage.css"></head>
<body onload="document.getElementById('loginfield').focus()">
<h2>WebApp management - login</h2>
<h4><%=self.Request.getSnakeletsVersion()%> @ <%=self.Request.getServerName()%></h4>
<form method="POST" action="login">
<p>Access is allowed only for authorised users.
<input type="hidden" name="action" value="login">
<table border="0" summary="login items">
<tr><td>Login name:</td><td><input id="loginfield" type="text" name="login"></td></tr>
<tr><td>Password:</td><td><input type="password" name="password"></td></tr>
<tr><td></td><td><input type="submit" value="Login" name="submit"></td></tr>
<tr><td></td><td><span style="color: red;"><%=error%></span></td></tr>
<tr><td></td><td><span style="color: grey;">Note: this is a default installation, you can log in with user 'test' and password 'test'.
<br>Change this in the web app's __init__.py file!</span></td></tr>
</table>
</form>
</body></html>
