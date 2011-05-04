<%@outputencoding=UTF-8%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%!-- This page has default session semantics; accessible without logging in --%>
<HTML>
<HEAD>
<TITLE>New profile created</TITLE>
<link rel="stylesheet" type="text/css" href="account.css">
</HEAD>
<%
if hasattr(self.RequestCtx,'name'):
	name=self.RequestCtx.name
	login=self.RequestCtx.login
else:
	self.abort("no user data")
%>
<BODY>
<h1>Profile created</h1>
<div class="body">
<p><strong>Thank you, &nbsp;<%=self.escape(name)%>.</strong></p>
<p>You have successfully created a profile, with login ID &nbsp;&nbsp;"<strong><%=self.escape(login)%></strong>".</p>
<p>We will not display the password you've entered again, so remember it well.</p>
<p>You can now <a href="login.y">Log in</a>.</p>
</div>
</BODY>
</HTML>

