<%@session=no%>
<%@import=import time,os%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>Snakelets Server</title>
<link rel="stylesheet" type="text/css" href="styles.css">
</head>
<body>
<h3>Welcome to the Snakelets server (<a href="manage/">MANAGE SERVER</a>)</h3>
<p>Time=<%=time.ctime()%> -- Your IP=<%=self.Request.getRealRemoteAddr()%></p>
<hr>
<p>Try the <a href="dir1/">directory listing support</a>.
<p>Go to the <a href="music/">mp3 jukebox</a> page
<p>There are various <a href="test/">test pages</a>.
<p><a href="account/">Account/login example</a>.
<p><a href="shop/">Shop example</a>.
<hr>
<h4>Quote of the moment:</h4>
<dl>
<dd>
<pre>
<%
quote=os.popen('fortune').read()
if quote:
	self.write(self.escape(quote))
else:
	self.write(self.escape("<< fortune program not installed >>"))
%>
</pre>
<%if os.name!='posix':
	self.write("<em>You're running on a non-Unix-ish OS, the output of the above 'fortune' program may be incorrect</em>")
%>
</dl>
<hr>
<address>&copy; Irmen de Jong  --  <%=self.Request.getServerSoftware()%></address>
</body>
</html>

