<%@gobbleWS=yes%>
<%@session=no%>
<%@import=import time,math%>
<%@inputencoding="iso-8859-15"%>
<%@outputencoding="UTF-8"%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head>
<title>python server pages</title>
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
</style>
</head>
<body>
<%
form=self.Request.getForm()
keys = form.keys()
keys.sort()
self.write("\n<H3>Form Contents:</H3><p>")
self.write(self.escape(repr(type(keys)))+" "+self.escape(repr(keys)))
if not keys:
	self.write("No form fields.")
%>
<dl>
<% for key in keys:%>
 <%if key:%>
   <dt><%=self.escape(key)%>: <i><%=self.escape(`type(form[key])`)%></i>
   <dd><%=self.escape(`form[key]`)%>
 <%end%>
<%end%>
</dl>
<hr>
<form method="POST" action="<%=self.getURL()%>">
<p>
<input type="text" name="arg" value="val1">
<input type="submit" name="submit" value="Submit form">
</form>
<hr>

<p>This page has been generated on
<%=time.ctime(time.time())%>

<hr>
<p>
Full url of this page: <%=self.escape(self.getFullURL())%>
<br>url of this page: <%=self.escape(self.getURL())%>
<br>request url: <%=self.escape(self.Request.getRequestURL())%>
</body>
</html>
