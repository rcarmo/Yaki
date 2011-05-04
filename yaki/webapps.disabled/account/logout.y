<%@outputencoding=UTF-8%>
<%@session=user%>
<%!-- This page has user session semantics; accessible only when logged in --%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<HTML>
<HEAD>
<TITLE>Logged out</TITLE>
<link rel="stylesheet" type="text/css" href="account.css">
</HEAD>
<BODY>
<h1>Bye bye!</h1>
<div class="body">
<p><strong>Bye Bye, <%=self.escape(self.User.name)%>. </strong></p>
<p><a href="login.y">Log in</a> again.</p>
</div>
</BODY>
</HTML>
<%
self.Request.deleteSession()
%>
