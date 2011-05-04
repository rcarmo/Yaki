<%!--============================================
    CREATE A NEW DIRECTORY.
================================================--%>
<%@inputencoding="ISO-8859-1"%>
<%@pagetemplate=TEMPLATE.y%>
<%@import=import os%>
<%
errorMsg = None

parentdir = self.SessionCtx.currentpath

fullparentdir=self.User.directory+parentdir

if self.Request.getParameter("create"):
    name=self.Request.getParameter("dirname")
    if not name:
        errorMsg="you must enter a name"
    else:
        name=os.path.normpath(fullparentdir+name)
        if not name.startswith(self.User.directory):
            errorMsg="won't write outside user directory tree"
        else:
            os.makedirs(name) 
            self.Yhttpredirect("browse?d="+parentdir)

if self.Request.getParameter("cancel"):
    self.Yhttpredirect("browse?d="+parentdir)
        
%>

<%!--=========================== DIRECTORY FORM ===================--%>
<div class="menucolumn">
</div>
<div class="contentcolumn">
<h1>Create a new directory</h1>
<h3>Target directory: <strong><%=self.escape(parentdir)%></strong></h3>
<form action="<%=self.getURL()%>" method="post" accept-charset="UTF-8">
Name of new directory:
<br /><input type="text" size="40" name="dirname" />
<br />
<input type="submit" name="create" value="Create directory" />
<input type="submit" name="cancel" value="Cancel" />
</form>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
</div>
