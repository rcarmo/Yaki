<%@authmethod=httpbasic;Test Realm%>
<%@authorized=dba,secretary%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Auth ok</title></head>
<body>
<p>If you can see this, the authentication succeeded.</p>
<p>** test: Try @session=no, yes, user</p>
<p>** test: Try @authmethod=httpbasic;realm, httpdigest;realm, loginpage;bla.html</p>
<hr>
<p>
<%if self.User:%>
There is a user: <%=self.User.userid%> called: <%=self.User.name%> with roles: <%=self.escape(str(self.User.privileges))%>
<%else:%>
There is no user.
<%end%>
<br>
<%if self.SessionCtx :%>
There is a Session.
<%else:%>
There is no Session.
<%end%>
<br><br>
<a href="testauth2.y">Go to page two.</a> (only works if you have the 'dba' role (mike), janet cannot access it. )
</body>
</html>
