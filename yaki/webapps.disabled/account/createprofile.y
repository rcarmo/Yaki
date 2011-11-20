<%@outputencoding=UTF-8%>
<%@inputencoding=windows-1252%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%!-- This page has default session semantics; accessible without logging in --%>
<%
fieldValues=getattr(self.RequestCtx,"fieldValues",{})
fieldErrors=getattr(self.RequestCtx,"fieldErrors",{})
%>
<HTML>
<HEAD>
<TITLE>Create user profile</TITLE>
<script type="text/javascript" src="setfocus.js"></script>
<link rel="stylesheet" type="text/css" href="account.css">
</HEAD>
<BODY onload="setFocus();">
<h1>Create new profile</h1>
<div class="body">
<p>Please fill in your details below.</p>
<form name="profile" method="post" action="account.sn?action=create" accept-charset="UTF-8">
<table summary="profile form">
<tr><td colspan="2"><span class="message"><%
if fieldErrors:
	self.write('Please correct the input.')
%></span></td></tr>
<tr><td>Your real name</td><td><input type="text" name="name" size="25" maxlength="100" value="<%=fieldValues.get("name","")%>"></td>
<td><span class="error"><%=fieldErrors.get("name","")%></span></td>
</tr>
<tr><td>Login name</td><td><input type="text" name="login" size="20" maxlength="20" value="<%=fieldValues.get("login","")%>"></td>
<td><span class="error"><%=fieldErrors.get("login","")%></span></td>
</tr>
<tr><td>Password</td><td><input type="password" name="password1" maxlength="20"></td>
<td><span class="error"><%=fieldErrors.get("password1","")%></span></td>
</tr>
<tr><td>Password (again)</td><td><input type="password" name="password2" maxlength="20"></td>
<td><span class="error"><%=fieldErrors.get("password2","")%></span></td>
</tr>
<tr><td></td><td><input type="submit" value="Create account"></td></tr>
</table>
</form>
</div>
</BODY>
</HTML>
