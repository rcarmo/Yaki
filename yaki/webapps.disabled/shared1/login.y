<%@session=yes%>
<%@inherit=snakeserver.user.LoginPage%>
<%

self.attemptLogin("index.y")       # call the base class, to attempt to log in 

# if we get here, the login failed.. (or we just logged out)
error=''
if self.Request.getParameter("login"):
    error="Invalid login"

%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><title>Shared Session Login</title></head>
<body onload="document.getElementById('loginfield').focus()">
<h2>Shared Session webapp #1 login</h2>
<form method="POST" action="login">
<p>Type the login information.
Recognised users are 'mike' with password 'apples',
and 'janet' with password 'pookie'.
<br>
<input type="hidden" name="action" value="login">
<table border="0" summary="login items">
<tr><td>Login name:</td><td><input id="loginfield" type="text" name="login"></td></tr>
<tr><td>Password:</td><td><input type="password" name="password"></td></tr>
<tr><td></td><td><input type="submit" value="Login" name="submit"></td></tr>
<tr><td></td><td><span style="color: red;"><%=error%></span></td></tr>
</table>
</form>
</body></html>
