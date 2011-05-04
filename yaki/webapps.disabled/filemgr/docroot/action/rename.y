<%@pagetemplate=TEMPLATE.y%>
<%@import=import os%>
<%

directory = self.SessionCtx.currentpath
selected_idx=int(self.Request.getParameter("i"))
if self.Request.getParameter("a")=="D_ren":
    selected = self.SessionCtx.dirlist[selected_idx]
else:
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

if self.Request.getParameter("rename"):
    newname=self.Request.getParameter("name")
    if not newname:
        errorMsg="you must enter a name"
    else:
        newname=os.path.normpath(self.User.directory+directory+newname)
        if not newname.startswith(self.User.directory):
            errorMsg="not allowed to rename outside user directory tree"
        else:
            if os.path.exists(newname):
                errorMsg="already exists: "+self.escape(self.Request.getParameter("name"))
            else:
                os.rename(filename,newname)
                self.Yhttpredirect(returndir)

%>
<div class="menucolumn">
</div>
<div class="contentcolumn">
<%if self.Request.getParameter("a")=="D_ren":%>
<h1>Rename a directory</h1>
<h3>Location: <%=self.escape(directory)%></h3>
<h3>Directory: <%=self.escape(selected)%></h3>
<%else:%>
<h1>Rename / move a file</h1>
<h3>Location: <%=self.escape(directory)%></h3>
<h3>File: <%=self.escape(selected)%></h3>
<%end%>
<form action="<%=self.URLprefix%>action/rename.y" method="post">
<%if self.Request.getParameter("a")=="D_ren":%>
New name:
<%else:%>
New location / name:
<%end%>
<br /><input type="text" size="50" name="name" value="<%=self.escape(selected)%>" />
<br />
<input type="submit" name="rename" value="Rename" />
<input type="submit" name="cancel" value="Cancel" />
<input type="hidden" name="a" value="<%=self.Request.getParameter("a")%>" />
<input type="hidden" name="i" value="<%=selected_idx%>" />
</form>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
</div>
