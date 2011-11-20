<%@session=yes%>
<%@import=import gc, time%>
<%
now = len(gc.get_objects())
prev = int(self.Request.getParameter("previous",0))
delta=str(now-prev)
%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Memory usage</title></head>
<body>
<h1>Memory usage ypage</h1>
<p>measured at <%=time.strftime("%c")%></p>
<p><strong>Python memory usage: <%=now%> objects (delta=<%=delta%>)</strong></p>
<p><a href="memory.y?previous=<%=now%>">Measure again</a></p>
<p><a href="memory.sn?previous=<%=now%>">Measure again (with snakelet)</a></p>
</body>
</html>
