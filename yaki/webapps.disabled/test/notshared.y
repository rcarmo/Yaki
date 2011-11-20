<%@session=yes%>
<%@import=import time%>
<%!-- *************************************************
      This page is used for the shared session example
      (webapps shared1 and shared2)
   ************************************************* --%>
<%

session=self.Request.getSession()

%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
	<title>Shared session example (test check page)</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">
<!--
body,td,th {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 10pt;
	color: #000000;
}
body {
	background-color: #EEEEFF;
}
h1 { font-size: 14pt; }
h2 { font-size: 12pt; }
-->
</style></head>
<body>
	<h1>Shared session example; test check page</h1>
<p>
This page is in a a different webapp (Test) that does not have
shared session configured. So it has its own session,
and you should see below that the information on it is
indeed different from the session that is shared in the two
shared session webapps:
<%if self.User:%>
<p><em>Username:</em> <%=self.User.userid%>
<br><em>Privileges:</em> <%="; ".join(self.User.privileges)%>
<%else:%>
<p><em>There is no User object on the session</em>
<%end%>
<br><em>Session ID:</em> <%=session.getID()%> (<%=time.ctime(session.createtime)%>)
<br><em>Shared?:</em> <%=session.shared%> 
<br><em>counter:</em> <%=getattr(self.SessionCtx,"counter","(there is no counter on the session)")%> 
<p>
If you now visit <a href="<%=url('../shared1/')%>">the shared-session webapp</a> again,
you will see that you are still logged in there (in a different session).
<hr>
<address>version: <%=self.Request.getSnakeletsVersion()%></address>
</body>
</html>

