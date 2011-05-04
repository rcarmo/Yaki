<%!--============================================
    UPLOAD A BUNCH OF NEW FILES.
================================================--%>
<%@inputencoding="ISO-8859-1"%>
<%@pagetemplate=TEMPLATE.y%>
<%@import=import os,shutil%>
<%

MAXPOSTSIZE=20*1024*1024

self.Request.setMaxPOSTsize(MAXPOSTSIZE)

directory = self.SessionCtx.currentpath

errorMsg = None

if self.Request.getParameter("upload"):
    filenames=[]
    form=self.Request.getForm()
    if form.get("f1"):
        filenames.append(form.get("f1"))
    if form.get("f2"):
        filenames.append(form.get("f2"))
    if form.get("f3"):
        filenames.append(form.get("f3"))
    if form.get("f4"):
        filenames.append(form.get("f4"))
    if form.get("f5"):
        filenames.append(form.get("f5"))
    for f in filenames:
        filename2=self.User.directory+'/'+directory[1:]+f.filename
        if os.path.exists(filename2):
            errorMsg="File already exists: "+f.filename
            break
        shutil.copyfileobj(f.file, open(filename2,"wb"))
    if not errorMsg:
        self.Yhttpredirect("browse?d="+directory)
if self.Request.getParameter("cancel"):
    self.Yhttpredirect("browse?d="+directory)
        
%>

<%!--=========================== UPLOAD FORM ===================--%>
<div class="menucolumn">
</div>
<div class="contentcolumn">
<h1>Upload files</h1>
<%if errorMsg:%>
<p><span class="error"><%=errorMsg%></span></p>
<%end%>
<h3>Target directory: <strong><%=self.escape(directory)%></strong></h3>
<form action="<%=self.getURL()%>" method="post" enctype="multipart/form-data">
<p><input type="file" name="f1" size="50"/></p>
<p><input type="file" name="f2" size="50" /></p>
<p><input type="file" name="f3" size="50" /></p>
<p><input type="file" name="f4" size="50" /></p>
<p><input type="file" name="f5" size="50" /></p>
<p>
<input type="submit" name="upload" value="Upload file(s)" />
<input type="reset" value="Clear" />
<input type="submit" name="cancel" value="Cancel" />
</p>
<p>Note: the total upload size may not exceed <%="%.1f" % (MAXPOSTSIZE/1024.0/1024.0)%> Mb</p>
</form>
</div>
