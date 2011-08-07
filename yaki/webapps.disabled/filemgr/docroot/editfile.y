<%!--============================================
    CREATE/EDIT A FILE.
================================================--%>
<%@inputencoding="ISO-8859-1"%>
<%@pagetemplate=TEMPLATE.y%>
<%@import=import os%>
<%
FILEENCODING="iso-8859-15"

self.Request.setEncoding("UTF-8")
edit = self.Request.getParameter("edit") or getattr(self.RequestCtx, "edit", False)
errorMsg = None

directory = self.SessionCtx.currentpath

if edit:
    selected_idx=int(self.Request.getParameter("i"))
    filename = self.SessionCtx.filelist[selected_idx]
    fullfilename=self.User.directory+directory+filename
    try:
        text=open(fullfilename,"r").read().decode(FILEENCODING)
    except Exception,x:
        errorMsg="Error loading file: "+str(x)
        text="**** COULD NOT LOAD THE FILE****\n"+str(x)
    
else:
    filename=self.Request.getParameter("filename")
    text=self.Request.getParameter("text").encode(FILEENCODING)

if self.Request.getParameter("create") or self.Request.getParameter("save"):
    if filename and text:
        filename2=os.path.normpath(self.User.directory+directory+filename)
        if not filename2.startswith(self.User.directory):
            errorMsg="won't write outside user directory base"
        else:
            text=text.replace("\r\n","\n")
            if (not self.Request.getParameter("save")) and os.path.exists(filename2):
                errorMsg="File already exists"
            else:
                open(filename2,"w").write(text)
                self.Yhttpredirect("browse?d="+directory)
if self.Request.getParameter("cancel"):
    self.Yhttpredirect("browse?d="+directory)
        
%>

<%!--=========================== FILE FORM ===================--%>
<div class="menucolumn">
</div>
<div class="contentcolumn">
<%if edit:%>
<h1>Edit file</h1>
<%else:%>
<h1>Create a new file</h1>
<%end%>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
<%if edit:%>
<h3>Target directory: <strong><%=self.escape(directory)%></strong></h3>
<h3>File name: <strong><%=self.escape(filename)%></strong></h3>
<%else:%>
<h3>Target directory: <strong><%=self.escape(directory)%></strong></h3>
<%end%>
<form action="<%=self.getURL()%>" method="post" accept-charset="UTF-8">
<p>
<%if edit:%>
<input type="hidden" name="filename" value="<%=self.escape(filename)%>"/>
<%else:%>
File name: <input type="text" size="40" name="filename" value="<%=self.escape(filename)%>"/>
<br />
<%end%>
<textarea cols="100" rows="25" name="text"><%=self.escape(text)%></textarea>
<br/>
<%if edit:%>
<input type="submit" name="save" value="Save file" />
<%else:%>
<input type="submit" name="create" value="Create file" />
<input type="reset" value="Clear" />
<%end%>
<input type="submit" name="cancel" value="Cancel" />
</p>
</form>
<p><em>Files will be saved using <%=FILEENCODING%> character-encoding.</em></p>
</div>
