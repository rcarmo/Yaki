<%@session=user%>
<%@pagetemplate="manage_template.y"%>
<%@pagetemplatearg=title=Server info%>
<%@authorized=admin%>
<%@import=import sys,gc,os%>
<%@import=import snakeserver.util as snakelets_util%>
<script type="text/javascript">
function askShutdown()
{
	if (confirm("Really shut down the server?"))
	{
		window.location="manage.sn?action=shutdown";
	}
}
</script>
<div class="panel">
<table summary="server information">
<tr><th colspan="2"><h3><%=self.Request.getSnakeletsVersion()%> @ <%=self.Request.getServerName()%>
</h3><h3>Server info</h3></th></tr>
<tr class="actions"><td><em>Actions:</em></td><td><a href="#" onclick="askShutdown()">shutdown</a> | <a href="access_log">access log stats</a></td></tr>
<tr class="actions"><td>&nbsp;</td><td><%=getattr(self.RequestCtx, "actionmsg", None) or "&nbsp;"%></td></tr>
<tr><td>software</td><td><%=self.Request.getServerSoftware()%></td></tr>
<tr><td>IP : port</td><td><%=self.Request.getServerIP()%> : <%=self.Request.getServerPort()%></td></tr>
<tr><td>servername</td><td><%=self.Request.getServerName()%></td></tr>
<tr><td>real hostname</td><td><%=self.Request.getRealServerName()%></td></tr>
<tr><td>running as user/group</td>
<td>
<%
curr=snakelets_util.getCurrentUserAndGroupId()
curr_names=snakelets_util.getCurrentUserAndGroupName()
%><%=curr%><%=curr_names%>
</td></tr>
<tr><td>URL prefix</td><td><%=self.Request.server.server.serverURLprefix or "<em>none</em>"%></td></tr>
<tr><td>protocol</td><td><%=self.Request.getServerProtocol()%></td></tr>
<tr><td>base URL</td><td><a href="<%=self.Request.getBaseURL()%>"><%=self.Request.getBaseURL()%></a></td></tr>
<tr><td>Uptime</td><td><%='%d days, %d hours, %d minutes, %d seconds' % self.Request.server.server.getUpTime()%></td>
<tr><td>Using Virtual Hosting</td><td><%=self.Request.server.server.useVirtualHosts%> (<a href="<%=self.URLprefix%>webapps">show configuration</a>)</td></tr>
<tr><td># Requests processed</td><td><%=self.Request.server.server.requestCounter%></td></tr>
<tr><td># Python Objects</td><td><%=len(gc.get_objects())%></td></tr>
<tr><td>Python module import path</td><td>
<%
pythonpath = os.environ.get("PYTHONPATH","").split(os.pathsep)
for path in sys.path:
    if path in pythonpath:
        self.write("<em>"+path+"</em>")
    else:
        self.write(path)
    self.write("<br>");
%>
<sub><em>Italic path components are defined in $PYTHONPATH</em></sub></td></tr>
</table>

<%!-- ************************************

		Uncomment this to show memory usage (referring objects)
<p>
All webapp referrers:
<br>
<%

for ( (vhost, url), webapp) in self.Request.server.server.allWebApps.items():
	self.write("<strong>[%s] %s --> </strong>" % (vhost,url))
	self.write("%d refering objects" % len(gc.get_referrers(webapp)))
	self.write("<br>\n")

%>
</p>

********************************** --%>


</div>
