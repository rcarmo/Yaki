<%@session=user%>
<%@outputencoding=iso-8859-15%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%!-- This page has user session semantics; accessible only when logged in --%>
<HTML>
<HEAD>
<TITLE>Login</TITLE>
<link rel="stylesheet" type="text/css" href="account.css">
</HEAD>
<BODY>
<h1>Logged in</h1>
<div class="body">
<p><strong>Hello, <%=self.escape(self.User.name)%>.</strong></p>
<p>You can <a href="viewprofile.y">view</a> your profile.</p>
<p>Or <a href="logout.y">Log out</a> again.</p>
</div>
</BODY>
</HTML>

