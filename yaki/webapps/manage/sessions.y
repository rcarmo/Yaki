<%@pagetemplate="manage_template.y"%>
<%@pagetemplatearg=title=Session info%>
<%@import=import time,urllib%>
<%
name=self.Request.getParameter("webapp")
vhost=self.Request.getParameter("vhost")
webapp=self.getWebApp().server.allWebApps.get( (vhost,name) )
urlname=urllib.quote_plus(name)
actionMsg = getattr(self.RequestCtx, "actionmsg", "")
%>
<script type="text/javascript">
<!--
function askKillSession(id,vhost,urlname)
{
	var answer=confirm("Really kill this session?")
	if (answer)
	{
		window.location="manage.sn?action=killsession&id="+id+"&vhost="+vhost+"&webapp="+urlname;
	}
}
function askKillAll(vhost, urlname)
{
	var answer=confirm("Really kill all sessions?")
	if (answer)
	{
		window.location="manage.sn?action=killsession&id=all&vhost="+vhost+"&webapp="+urlname;
	}
}
-->
</script>
<div class="panel">
<table summary="session information">
<tr><th colspan="2"><h3>Sessions of WebApp '<%=webapp.getName()[1]%>'</h3></th></tr>
<tr class="actions"><td>Actions:</td><td><a href="#" onclick="askKillAll('<%=vhost%>', '<%=urlname%>')">Kill all</a></td></tr>
<tr><td colspan="2"><%=len(webapp.sessions)%> active web sessions.</td></tr>
<tr><td  colspan="2">
<table class="snakeletinfo" summary="sessions">
<tr><th>IP adress</th><th>age</th><th>unused</th><th>User?</th><th>SessionID</th><th>Action</th></tr>
<%
sessions=[ (session.createtime, session) for session in  webapp.sessions.values() ]
sessions.sort()
for createtime, session in sessions:%>
	<tr>
		<td><%=session.getRemoteAddr()%></td>
		<td><%=int(time.time()-session.createtime)%> sec.</td>
		<td><%=int(time.time()-session.lastused)%> sec.</td>
		<td><%if session.getLoggedInUser():%><%=self.escape(session.getLoggedInUser().userid)%><%else:%>-<%end%></td>
		<td style="font-size: 75%;"><%=session.getID()%></td>
		<td><a href="#" onclick="askKillSession('<%=session.getID()%>','<%=vhost%>','<%=urlname%>')">kill</a></td>
	</tr>
<%end%>
</table>
</td></tr>
</table>
</div>
