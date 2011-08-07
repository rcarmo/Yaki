<%@session=user%>
<%@pagetemplate="manage_template.y"%>
<%@pagetemplatearg=title=WebApp info%>
<%@authorized=admin%>
<%@import=import urllib%>
<script type="text/javascript">
<!--
function askDisable(name, vhost, urlname)
{
	var answer=confirm("Really disable WebApp '"+name+"'  ["+vhost+"] ?");
	if (answer)
	{
		window.location='manage.sn?action=disable&vhost='+vhost+'&name='+urlname;
	}
}
function askReload(name, vhost, urlname)
{
	var answer=confirm("Really reload WebApp '"+name+"'  ["+vhost+"] ?\n(Note that reloading might not reload all relevant modules...)");
	if (answer)
	{
		window.location='manage.sn?action=reload&vhost='+vhost+'&name='+urlname;
	}
}
function askDestroy(name, vhost, urlname)
{
	var answer=confirm("Really destroy WebApp '"+name+"'  ["+vhost+"] ?");
	if (answer)
	{
		window.location='manage.sn?action=destroy&vhost='+vhost+'&name='+urlname;
	}
}
-->
</script>
<%
name=self.Request.getParameter("name")
vhost=self.Request.getParameter("vhost")

webapp=self.getWebApp().server.allWebApps.get( (vhost,name) )
urlname=urllib.quote_plus(name)
actionMsg = getattr(self.RequestCtx, "actionmsg", "")

def shortenURL(URL, maxlen):
	if len(URL)<=maxlen:
		return URL
	return URL[:7]+"....."+URL[-(maxlen-12):]

%>
<div class="panel">
<table summary="webapp info">
<%if not webapp:%>
<h3>WebApp '<%=name%>' &nbsp; [<%=vhost%>]</h3>
<%
available=self.getWebApp().server.configuredWebApps[vhost]
availableWebApp=False
for wa in available:
    if name==wa:
        availableWebApp=True
        break
%>
 <%if availableWebApp:%>
 <p>This web app is available but has not been loaded.</p>
 <p>The webapp might have been destroyed, or an error could have occured in the webapp initialisation code.
    More info should be available in the server logfile.</p>
 <p>If you think you've fixed it, you can try to reload the web application.</p>
<p>
<a href="manage.sn?action=reload&vhost=<%=vhost%>&realname=<%=name%>">reload</a>
</p>
 <%else:%>
  The web application name cannot be found. Has the application been renamed?
 <%end%>
<%else:%>
<tr><th colspan="2"><h3>WebApp '<%=webapp.getName()[1]%>' &nbsp; [<%=vhost%>]</h3></th></tr>
<tr class="actions"><td><em>Actions:</em></td><td><strong>
<a href="javascript:void()" onclick="askDisable('<%=name%>', '<%=vhost%>', '<%=urlname%>');return false;">disable</a>
| <a href="manage.sn?action=enable&amp;vhost=<%=vhost%>&amp;name=<%=urlname%>">enable</a>
| <a href="javascript:void()" onclick="askReload('<%=name%>', '<%=vhost%>', '<%=urlname%>'); return false;">reload</a>
| <a href="javascript:void()" onclick="askDestroy('<%=name%>','<%=vhost%>', '<%=urlname%>'); return false;">destroy</a>
| <a href="manage.sn?action=clearcache&amp;vhost=<%=vhost%>&amp;name=<%=urlname%>">clear cache</a>
</strong></td></tr>
<tr class="actions"><td>&nbsp;</td><td><%=actionMsg or "&nbsp;"%></td></tr>
<tr><td>name</td><td><%=webapp.getName()[1]%> &nbsp; &nbsp;
<%
if webapp.isEnabled():
	self.write("<span style=\"color: green;\">(enabled)</span>")
else:
	self.write("<em style=\"color:maroon;\">(DISABLED)</em>")
%>
</td></tr>
<tr><td>vhost</td><td><%='%s:%d' % webapp.getVirtualHost()%></td></tr>
<tr><td>urlprefix</td><td>
<a href="<%=('http://%s:%d' % webapp.getVirtualHost())+webapp.getURLprefix()%>"><%=webapp.getURLprefix()%></a>
</td></tr>
<tr><td>docroot</td><td><%=webapp.getDocRootPath()%></td></tr>
<tr><td>abs. path</td><td><%=webapp.getFileSystemPath()%></td></tr>
<tr><td>session timeout</td><td><%=webapp.sessionTimeoutSecs%></td></tr>
<tr><td>shared session?</td><td><%=webapp.sharedSession%></td></tr>
<tr><td>default request encoding</td><td><%=webapp.defaultRequestEncoding or '<em>not specified</em>'%></td></tr>
<tr><td>default content type</td><td><%=webapp.defaultContentType or '<em>not specified</em>'%></td></tr>
<tr><td>default output encoding</td><td><%=webapp.defaultOutputEncoding or '<em>not specified</em>'%></td></tr>
<tr><td>default template</td><td><%=webapp.defaultPageTemplate or '<em>not specified</em>'%></td></tr>
<tr><td>active sessions</td><td><%=len(webapp.sessions)%> <a href="sessions.y?vhost=<%=vhost%>&amp;webapp=<%=urlname%>">details</a></td></tr>
<tr><td valign="top">config</td><td><%=self.escape(str(webapp.getConfigItems()))%></td></tr>
<%
# gather snakelets info
snakelets=webapp.getSnakelets().items()
snakelets.sort()
%>
<tr><td valign="top">snakelets<br>(<%=len(snakelets)%>)</td><td>
<%for (url, snk) in snakelets:%>
<table class="snakeletinfo" summary="snakelet info">
<tr><th colspan="2">Snakelet info</th></tr>
<tr><td>description</td><td><%=snk.getDescription()%></td></tr>
<tr><td>url</td><td><%=snk.getURL()%></td></tr>
<tr><td>full url</td><td><a href="<%=snk.getFullURL()%>"><%=shortenURL(snk.getFullURL(),40)%></a></td></tr>
<%
sessionTxt = {
	Ypage.SESSION_NOT_NEEDED: "no",
	Ypage.SESSION_WANTED: "wanted",
	Ypage.SESSION_REQUIRED: "required",
	Ypage.SESSION_LOGIN_REQUIRED: "login required",
	Ypage.SESSION_DONTCREATE: "use if exists, but don't create new"
	} [ snk.requiresSession()]
%>
<tr><td>session?</td><td><%=sessionTxt%></td></tr>
<%if snk.allowCaching():%>
<tr><td>browser caching?</td><td>allowed</td></tr>
<%end%>
<tr><td>class</td><td><%=snk.__class__.__module__+'.'+snk.__class__.__name__%></td></tr>
</table>
<br>
<%end%>
<%if not snakelets:
	self.write("<em>none defined</em>")
%>
</td></tr>
<%end%>
</table>
</div>

