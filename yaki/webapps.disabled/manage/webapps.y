<%@session=user%>
<%@pagetemplate="manage_template.y"%>
<%@pagetemplatearg=title=WebApp/Vhost configuration%>
<%@authorized=admin%>
<%

server=self.Request.server.server

%>
<div class="panel">
<h3>Virtual Host config</h3>
<p>
<%if server.useVirtualHosts:%>
Virtual hosting is <strong>enabled</strong>.
<%else:%>
Virtual hosting is <strong>disabled</strong>.
<%end%>
<br><sub>It is configured in the WebApp init file.</sub>
<table summary="vhost config">
<tr><th colspan="2">Active configuration</th></tr>
<tr><td class="actions">WebApp deployments
<br><sub>Same list as main menu</sub></td><td>
<table class="snakeletinfo">
<%vhosts=server.virtualHosts.keys()
vhosts.sort()
for vhost in vhosts:
    webapps = server.virtualHosts[vhost]
    webapps.sort()
    self.write("<tr><td><span class=\"vhost\">%s</span></td><td><table class=\"noborders\">"  % vhost)
    if vhost in server.webRoots:
        self.write("<tr><td>%s</td><td> &nbsp; <em>(ROOT web app; /)</em></td></tr>" % server.webRoots[vhost].getName()[0])
    else:
        self.write('<tr><td colspan="2"><em>no ROOT webapp deployed</em></td></tr>')
    for w in webapps:
        self.write("<tr><td>%s</td><td> &nbsp; %s</td></tr>" % w.getName())
    self.write("</table></td></tr>")
%>
</table>
</td></tr>
<tr><td class="actions">VHost aliases
<br><sub>Maps vhosts to another vhost</sub></td><td>
    <table class="noborders">
    <%for vhost, target in server.vhostAliases.iteritems():%>
     <tr>
      <td><span class="vhost"><%=vhost%></span></td>
      <td>&nbsp;&rarr;&nbsp;</td>
      <td><span class="vhost"><%=target%></span></td>
     </tr>
    <%end%>
    </table>
</td></tr>
<tr><td class="actions">Fallback VHost
<br><sub>Used when no HTTP Host header is sent</sub></td><td><span class="vhost"><%='%s : %d' % server.defaultVirtualHost%></span></td></tr>
</table>
<br>
<table summary="available webapps">
<tr><th colspan="3">All Available WebApps (in the webapp dir)</th></tr>
<tr class="actions"><td>WebApp</td><td>Deployed on</td><td>Notes</td></tr>
<%
_allWA = set()
for vhost in server.configuredWebApps:
    _allWA.update(server.configuredWebApps[vhost])
_allWA = [ (w.lower(), w) for w in _allWA]
_allWA.sort()
allWA=[x[1] for x in _allWA]
for wa in allWA:
    deployments=[]
    for vhost, webapps in server.virtualHosts.iteritems():
        if wa in [w.getName()[0] for w in webapps]:
            deployments.append(vhost)
    for vhost, webapp in server.webRoots.iteritems():
        if wa==webapp.getName()[0]:
            deployments.append(vhost)
    deployments.sort()
    deployments=['<span class="vhost">%s</span>' % vhost for vhost in deployments]
    self.write("<tr><td>%s</td><td>" % wa)  
    if deployments:
        self.write("&nbsp;;&nbsp;".join(deployments))
        self.write("</td></tr>")
    else:
        self.write('<span class="message">not deployed</span>')
        self.write('</td><td>Reload webapp using the menu</td></tr>')
%>
</table>

</div>
