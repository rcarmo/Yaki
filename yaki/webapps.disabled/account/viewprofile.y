<%@session=user%>
<%@outputencoding=iso-8859-15%>
<%@inputencoding=windows-1252%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%!-- This page has user session semantics; accessible only when logged in --%>
<%
fieldValues=getattr(self.RequestCtx,"fieldValues",{})
fieldErrors=getattr(self.RequestCtx,"fieldErrors",{})
%>
<HTML>
<HEAD>
<script type="text/javascript" src="setfocus.js"></script>
<TITLE>User profile</TITLE>
<link rel="stylesheet" type="text/css" href="account.css">
</HEAD>
<BODY onload="setFocus();">
<h1>View Profile</h1>
<div class="body">
<p><strong>User profile of <%=self.escape(self.User.name)%></strong></p>
<p>You can edit your profile below.</p>
<form name="form1" method="post" action="account.sn?action=update" accept-charset="UTF-8">
<table summary="profile">
    <tr>
		<td>password hash</td>
		<td><tt><%=self.User.password.encode("hex")%></tt></td>
    </tr>
	<tr>
		<td>Your real name</td>
		<td><input type="text" name="name" size="25" maxlength="100" value="<%=self.escape(self.User.name)%>"></td>
		<td><span class="error"><%=fieldErrors.get("name","")%></span></td>
	</tr>
	<tr><td colspan="2">If you want to change your password, you can do so below.</td></tr>
	<tr>
		<td>Old password</td>
		<td><input type="password" name="password_old" maxlength="20"></td>
		<td><span class="error"><%=fieldErrors.get("password_old","")%></span></td>
	</tr>
	<tr>
		<td>New password</td>
		<td><input type="password" name="password_new1" maxlength="20"></td>
		<td><span class="error"><%=fieldErrors.get("password_new1","")%></span></td>
	</tr>
	<tr>
		<td>New password (again)</td>
		<td><input type="password" name="password_new2" maxlength="20"></td>
		<td><span class="error"><%=fieldErrors.get("password_new2","")%></span></td>
	</tr>
	<tr>
		<td></td>
		<td><input type="submit" value="Update profile"></td>
	</tr>
</table>
</form>
</div>
</BODY>
</HTML>
