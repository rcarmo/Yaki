<%@session=user%>
<%@authmethod=httpbasic%>
<%@authorized=dba%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Auth ok (2)</title></head>
<body>
<p>This is page two.
<p>If you can see this, the authentication succeeded.</p>
<hr>
<p>
<%if self.User:%>
There is a user: <%=self.User.userid%> with roles: <%=self.escape(str(self.User.privileges))%>
<%else:%>
There is no user.
<%end%>
<br>
<%if self.SessionCtx :%>
There is a Session.
<%else:%>
There is no Session.
<%end%>
<p>
<a href="testauth.y">Back to page one.</a>
</body>
</html>
