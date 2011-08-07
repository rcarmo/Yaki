<%@pagetemplate=TEMPLATE.y%>
<%@import=import os,shutil%>
<%

directory = self.SessionCtx.currentpath
selected_idx=int(self.Request.getParameter("i"))
selected = self.SessionCtx.filelist[selected_idx]

returndir=self.URLprefix+"browse?d="+directory
if not returndir.endswith('/'):
    returndir+='/'

if self.Request.getParameter("cancel"):
    self.Yhttpredirect(returndir)

errorMsg=None

if not directory or not selected:
    self.abort("illegal arguments")

filename=os.path.normpath(self.User.directory+directory+selected)

if self.Request.getParameter("copy"):
    newname=self.Request.getParameter("name")
    if not newname:
        errorMsg="you must enter a target name"
    else:
        newname=os.path.normpath(self.User.directory+directory+newname)
        if not newname.startswith(self.User.directory):
            errorMsg="not allowed to copy outside user directory tree"
        else:
            if os.path.exists(newname):
                errorMsg="already exists: "+self.escape(self.Request.getParameter("name"))
            else:
                shutil.copy(filename,newname)
                self.Yhttpredirect(returndir)
    
%>
<div class="menucolumn">
</div>
<div class="contentcolumn">
<h1>Copy a file</h1>
<h3>Source location: <%=self.escape(directory)%></h3>
<h3>Source file: <%=self.escape(selected)%></h3>
<form action="<%=self.URLprefix%>action/copy.y" method="post">
Target location / name:
<br /><input type="text" size="50" name="name" value="Copy of <%=self.escape(selected)%>" />
<br />
<input type="submit" name="copy" value="Copy" />
<input type="submit" name="cancel" value="Cancel" />
<input type="hidden" name="i" value="<%=selected_idx%>" />
</form>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
</div>
