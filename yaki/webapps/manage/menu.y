<%@import=import time%>
<div class="menu">
<p><span style="color: gray;"><span style="font-weight: bold;"><%=self.User.userid%></span> (<a href="login?logout=yes">logout</a>)</span>
<br><span style="color: gray; font-size: 80%;"><%=time.ctime()%>
<br><%='%s:%d' % self.getWebApp().getVirtualHost() %></span>
</p>
<p><span style="font-size: large;">&bull;</span> Server:<br><a href="serverinfo"> Server info &raquo;</a></p>
<p><span style="font-size: large;">&bull;</span> WebApps - available:<br><a href="webapps"> Show list &amp; vhosts &raquo;</a></p>
<p><span style="font-size: large;">&bull;</span> WebApps - deployed:<br>

<%
def showWA(webappname,enabled, url, virtualhost):%> 
	<span class="light-<%=enabled%>">&bull;</span>
	<strong><a href="webappinfo?vhost=<%=self.urlescape(virtualhost)%>&amp;name=<%=self.urlescape(url)%>"><span class="webappname-<%=enabled%>"><%=url%></span></a></strong><br>
<sup>&nbsp;&nbsp;&nbsp;&nbsp; <a href="webappinfo?name=<%=self.urlescape(url)%>&amp;vhost=<%=self.urlescape(virtualhost)%>"><%=webappname%></a></sup><br>
<%end%>


<%
wroots = self.getWebApp().server.webRoots
configuredApps = self.getWebApp().server.configuredWebApps   #  vhost->webappname
allVhosts=configuredApps.keys()
allVhosts.sort()

for vhost in allVhosts:
    self.write('<br><span class="vhost">'+vhost+'</span><br>')
    webappsForVhost=configuredApps[vhost][:]
    webappsForVhost.sort()
    # first, check for a root webapp
    wa=wroots.get(vhost)
    if wa:
        webappsForVhost.remove(wa.getName()[0])  # remove ROOT webapp from the list
        if wa.isEnabled():
            enabled='enabled'
        else:
            enabled='disabled'
        showWA(wa.getName()[1], enabled,wa.urlprefix,vhost)

    # other webapps
    for webappname in webappsForVhost:
        webapp=self.getWebApp().server.allWebApps.get( (vhost,'/'+webappname+'/') )
    	if webapp:
            if webapp.isEnabled():
                enabled='enabled'
            else:
                enabled='disabled'
    	    showWA(webapp.getName()[1],enabled,webapp.urlprefix,vhost) 
    	else:
    	    showWA(webappname,"error",webappname,vhost)   # this webapp wasn't loaded due to an error
%>

</p>
<div class="createnotice">This server is running <a href="http://www.python.org">Python</a>
with <a href="http://snakelets.sourceforge.net">Snakelets</a> software, created by
<a href="http://www.razorvine.net">Irmen de Jong</a>.</div>
</div>
