<%@pagetemplate=TEMPLATE.y%>
<%@import=import os,time,math%>
<%@pagetemplatearg=nofocus=true%>
<%

directory = self.SessionCtx.currentpath
selected_idx=int(self.Request.getParameter("i"))
if self.Request.getParameter("a")=="D_del":
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

if self.Request.getParameter("delete"):
    if self.Request.getParameter("a")=="D_del":
        try:
            os.rmdir(filename)
            self.Yhttpredirect(returndir)
        except EnvironmentError,x:
            errorMsg = str(x)
    else:
        os.remove(filename)
        self.Yhttpredirect(returndir)
            

stats=os.stat(filename)

%>
<div class="menucolumn">
</div>
<div class="contentcolumn">
<%if self.Request.getParameter("a")=="D_del":%>
<h1>Delete an empty directory</h1>
<h3>Location: <%=self.escape(directory)%></h3>
<h3>Directory: <%=self.escape(selected)%></h3>
<h5>Time: <%=time.strftime("%d %b %Y  %H:%M:%S",time.localtime(stats.st_mtime))%></h5>
<%else:%>
<h1>Delete a file</h1>
<h3>Location: <%=self.escape(directory)%></h3>
<h3>File: <%=self.escape(selected)%></h3>
<h5>Size: <%=int(math.ceil(stats.st_size/1024.0))%> Kb &bull; Time: <%=time.strftime("%d %b %Y  %H:%M:%S",time.localtime(stats.st_mtime))%></h5>
<%end%>
<form action="<%=self.URLprefix%>action/delete.y" method="post">
<%if self.Request.getParameter("a")=="D_del":%>
Really delete this directory?
<%else:%>
Really delete this file?
<%end%>
<br />
<input type="submit" name="delete" value="Delete it" />
<input type="submit" name="cancel" value="Cancel" />
<input type="hidden" name="a" value="<%=self.Request.getParameter("a")%>" />
<input type="hidden" name="i" value="<%=selected_idx%>" />
</form>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
</div>
