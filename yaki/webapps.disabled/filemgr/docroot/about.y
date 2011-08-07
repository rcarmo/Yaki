<%!--=========================================

    File Manager "About" page.

============================================--%>
<%@inputencoding="ISO-8859-1"%>
<%@pagetemplate=TEMPLATE.y%>
<%@session=dontcreate%>
<%

from filemgr import VERSION
HOMEPAGE = "http://snakelets.sourceforge.net/filemgr/"

%>
<div class="contentcolumn">
<h3>About this website</h3>
<table cellspacing="10">
<tr><td align="right">Powered by:</td> <td><strong>File Manager <%=VERSION%></strong></td> </tr>  
<tr><td /><td><a href="<%=self.escape(HOMEPAGE)%>"><%=self.escape(HOMEPAGE)%></a></td> </tr>  
<tr><td /><td>(Created by Irmen de Jong)</td> </tr>  
<tr><td align="right">Software License:</td><td><a href="http://www.gnu.org/copyleft/gpl.html">GNU GPL</a></td> </tr>  
<tr><td align="right">Running on:</td><td><%=self.Request.getServerSoftware()%></td> </tr>  
</table>
<br /><br />
<%
back=self.Request.getReferer()
if not back:
    back=self.URLprefix
%>
<p><a href="<%=back%>">&larr; go back</a></p>
</div>
