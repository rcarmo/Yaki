<%@session=yes%>
<%@outputencoding=iso-8859-15%>
<%@inputencoding=windows-1252%>
<%!-- This page has regular session semantics; accessible without logging in --%>
<%@inherit=snakeserver.user.LoginPage%>
<%!--

  Notice that this login.y page is also its own form submit target.
  It inherits from the Snakelets-provided LoginPage (look above).
  This means that you can let Snakelets deal with the login attempt,
  by using a single method call: attemptLogin()

--%>
<%

# you can set the form encoding per page: self.Request.setEncoding("UTF-8")
#... but this webapp has defined a global defaultRequestEncoding in the webapp init file.

self.attemptLogin("loggedin.y")       # call the base class, to attempt to log in 

# If the login succeeded, we are forwarded to the target page.
# If we're still here, the login failed..
error=''
if self.Request.getParameter("login"):
    error="Invalid login"

%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head>
<script type="text/javascript" src="setfocus.js"></script>
<title>Login</title>
<link rel="stylesheet" type="text/css" href="account.css">
</head>
<body onload="setFocus();">
<h1>Login</h1> 
<div class="body">
  <p>Enter a valid login name and password.</p>
  <div class="form">
    <form action="<%=self.getURL()%>" name="login" method="post" accept-charset="UTF-8">
      <table summary="input form">
        <tr> 
          <td>Login</td>
          <td><input type="text" size="21" maxlength="20" name="login"></td>
        </tr>
        <tr> 
          <td>Password</td>
          <td><input type="password" size="21" maxlength="20" name="password"></td>
        </tr>
        <tr> 
          <td></td>
          <td><input type="submit" class="button" value="Login"> &nbsp; <span class="error"><%=error%></span></td>
        </tr>
		  <tr><td></td><td colspan="2">No account? <a href="createprofile.y">Create a new one</a>.</td></tr>
      </table>
	</form>
</div>
<p><em>Note: for test purposes, there is a built-in user 'test' with password 'test'.</em></p>
<br><br><br>
<h3>What's this all about?</h3>
<p>This example web application implements the most important aspects
of account management and user authentication (accounts with login+password combination).
</p>
<p>The implementation of this web app uses Snakelet's built-in functions for
safe user authentication management. The only thing missing is an encrypted HTTPS connection;
sorry but that is not -yet- supported by Snakelets. This means that your login and
password information is currently send in clear text over the network.
</p>
</div>
</body>
</html>
