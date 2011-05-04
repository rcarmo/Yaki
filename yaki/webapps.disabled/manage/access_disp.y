<%!--
   Access.log scanner
   Based on a contribution by Vincent Delft
--%>
<html>
<head><title>access.log fragment</title></head>
<body style="font-size: 80%">
<div align="center"><a href="javascript:window.history.go(-1);">Back</a></div>
<hr>
<%
import urllib
r=self.SessionCtx.analyzer
date=self.Request.getParameter('date',None)
key=self.Request.getParameter('key',None)
data=self.Request.getParameter('data',None)
%>
<%
for item in r.getRecords(date,key,data):
    self.write('<br>%s\n' % item)
%>
<hr>
<div align="center"><a href="javascript:window.history.go(-1);">Back</a></div>
</body>
</html>
