<%@session=user%>
<%@authmethod=loginpage;login.y%>
<%@import=import time%>
<%

session=self.Request.getSession()

if hasattr(self.SessionCtx,"counter"):
    self.SessionCtx.counter+=1
else:
    self.SessionCtx.counter=1

%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
	<title>Shared session example (webapp 1)</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">
<!--
body,td,th {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 10pt;
	color: #000000;
}
body {
	background-color: #EEFFFF;
}
h1 { font-size: 14pt; }
h2 { font-size: 12pt; }
-->
</style></head>
<body>
	<h1>Shared session example; webapp #1</h1>
<p>
If you can read this text, you have been logged in.
<p><em>Username:</em> <%=self.User.userid%>
<br><em>Privileges:</em> <%="; ".join(self.User.privileges)%>
<br><em>Session ID:</em> <%=session.getID()%> (<%=time.ctime(session.createtime)%>)
<br><em>Shared?:</em> <%=session.shared%> 
<br><em>counter:</em> <%=self.SessionCtx.counter%> (refresh page to count up)
<p>
If you now visit <a href="<%=url('../shared2/')%>">the other shared-session webapp</a>,
you will see that you are logged in there too, with the exact same session information (id, counter).
It shares your current session and user information.
<p>However, if you visit <a href="<%=url('../test/notshared.y')%>">the notshared test page</a>
of the Test webapp,
you will see that you are not logged in there. It does <em>not</em> share this session.
<hr>
<address>version: <%=self.Request.getSnakeletsVersion()%></address>
</body>
</html>

