<%@pagetemplate=TEMPLATE.y%>
<%@import=import os%>
<%

directory = self.SessionCtx.currentpath

returndir=self.URLprefix+"browse?d="+directory
if not returndir.endswith('/'):
    returndir+='/'

if self.Request.getParameter("cancel"):
    self.Yhttpredirect(returndir)

errorMsg=None
newmode=None
if self.Request.getParameter("chmod"):
    if not self.Request.getParameter("mode"):
        self.abort("illegal mode")
    try:
        newmode=int(self.Request.getParameter("mode"),8)
        if newmode>0777:
            newmode=None
            raise ValueError("too large")
    except Exception,x:
        errorMsg="invalid mode number (use 000-777 octal codes only)"

selected_idx=int(self.Request.getParameter("i"))
selected = self.SessionCtx.filelist[selected_idx]
filename=os.path.normpath(self.User.directory+directory+selected)

if newmode is not None:
    os.chmod(filename, newmode)
    self.Yhttpredirect(returndir)

    
mode=os.stat(filename).st_mode & 0777

%>
<div class="menucolumn">
<p>Examples:</p>
<hr />
<p>000 = unaccessible for all</p>
<p>600 = read/write for user</p>
<p>777 = r/w/x for all</p>
<p>644 = r/w for user, r for other</p>
<br />
<p>(it is an octal code;
see the <a href="http://www.netadmintools.com/html/1chmod.man.html">chmod</a> manpage)</p>
</div>
<div class="contentcolumn">
<h1>Change file protection mode</h1>
<h3>Location: <%=self.escape(directory)%></h3>
<h3>File: <%=self.escape(selected)%></h3>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
<form action="<%=self.URLprefix%>action/chmod.y" method="post">
File protection mode: <input type="number" size="4" maxlength="3" name="mode" value="<%="%03o" % mode%>" />
<input type="submit" name="chmod" value="Change mode" />
<input type="submit" name="cancel" value="Cancel" />
<input type="hidden" name="i" value="<%=selected_idx%>" />
</form>
</div>
