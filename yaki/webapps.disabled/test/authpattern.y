<%@authmethod=httpbasic;test realm%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Auth ok (2)</title></head>
<body>
<p>If you can see this, the authentication succeeded.</p>
<hr>
<p>
<%if self.User:%>
There is a user: <%=self.User.userid%> called: <%=self.User.name%> with roles: <%=self.escape(str(self.User.privileges))%>
<%else:%>
<strong style="color: maroon">There is no user!!! This is a security bug, because this
page is protected by an authorization pattern, and to let that work, a user must be present with correct privileges!
</strong>
<p>
<%end%>
<br>
<%if self.SessionCtx :%>
There is a Session.
<%else:%>
There is no Session.
<%end%>
</body>
</html>
