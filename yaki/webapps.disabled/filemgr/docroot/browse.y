<%!--=========================================

    Main browsing page.

============================================--%>
<%@inputencoding="ISO-8859-1"%>
<%@pagetemplate=TEMPLATE.y%>
<%@pagetemplatearg=nofocus=yes%>
<%@indent=4spaces%>
<%@import=import os,time,mimetypes,math%>
<%

if self.Request.getPathInfo():
    self.Yhttpredirect(self.getURL())
    
pathspec = self.Request.getParameter("d") or '/'

if "//" in pathspec or "/.." in pathspec:
    self.abort("relative paths not allowed")

self.SessionCtx.currentpath = pathspec      # store the current path on the session

path = os.path.normpath(self.User.directory+pathspec)
if not path.startswith(self.User.directory):
    self.abort("won't list a directory outside specified location")

if os.path.isdir(path) and pathspec and not pathspec.endswith('/'):
    self.abort("missing / at end")
    self.Yhttpredirect(self.URLprefix+"browse?d="+pathspec+'/')
    
# Caching directory lister, outputs (filelist,dirlist) tuple
# Based upon dircache.py
_listdir_cache = {}
def listdir(path):
	try:
		cached_mtime, files, directories = _listdir_cache[path]
		del _listdir_cache[path]
	except KeyError:
		cached_mtime, files, directories = -1, [], []
	mtime = os.stat(path)[8]
	if mtime != cached_mtime:
		lizt = os.listdir(path)
		files=[ f for f in lizt if os.path.isfile(os.path.join(path,f)) and not f[0]=='.' ]
		directories=[ d for d in lizt if os.path.isdir(os.path.join(path,d)) and not d[0]=='.' ]
	_listdir_cache[path] = mtime, files, directories
	return files,directories

files,dirs = listdir(path)
files.sort()
dirs.sort()

self.SessionCtx.dirlist = dirs      # store the current directory list on the session
self.SessionCtx.filelist = files      # store the current directory list on the session

%>
<div class="menucolumn">
<h2>Location</h2>
<%
tree=pathspec.split('/')[1:-1]   # split up the directories, strip the first and last /

i=1
self.write('<img src="img/sub.gif" alt="+" /> <a href="'+self.getURL()+'?d=/">(root)</a>\n')
returnpath="/"
for t in tree:
    returnpath=returnpath+t+'/'
    self.write("<br />")
    self.write("&nbsp; "*i)
    self.write('<img src="img/sub.gif" alt="+" /> <a href="'+self.getURL()+'?d='+returnpath+'">'+self.escape(t)+'</a>\n')
    i+=1
%>
<h2><%=len(dirs)%> Directories</h2>
<p>
<%for i,d in enumerate(dirs):%>
  <a href="action?a=D_del&amp;i=<%=i%>"><img title="delete" alt="D" src="img/trash.gif" /></a>
  <a href="action?a=D_ren&amp;i=<%=i%>"><img title="rename" alt="R" src="img/rename.gif" /></a>
  <a title="open" href="<%=self.escape("%s?d=%s%s/"%(self.getURL(),pathspec,d))%>"><%=self.escape(d)%></a> <br />
<%end%>
</p>
<p>
<img alt="" src="<%=self.URLprefix%>img/createdir.gif" /> <a title="create" href="<%=self.URLprefix%>createdir">Create new dir&hellip;</a>
</p>
</div>
<div class="contentcolumn">
<h2><%=len(files)%> Files in Location: <%=self.escape(self.SessionCtx.currentpath)%></h2>
<p>
<img alt="" src="<%=self.URLprefix%>img/form.gif" /> <a href="<%=self.URLprefix%>uploadfiles">Upload files&hellip;</a>
&nbsp; &nbsp;
<img alt="" src="<%=self.URLprefix%>img/createfile.gif" /> <a href="<%=self.URLprefix%>editfile">Create new text file&hellip;</a>
<%
parentdir=None
if tree:
    if len(tree)>1:
        parentdir='/'+tree[-2]+'/'
    else:
        parentdir='/'
if parentdir:%>
&nbsp; &nbsp;
<img alt="" src="<%=self.URLprefix%>img/scrollup.gif" /> <a href="<%=self.getURL()+'?d='+parentdir%>">Parent directory</a>
<%end%>
</p>
<%if not files:%><p>(no files)</p>
<%else:%>
  <br />
  <table class="filelist">
  <tr>
  <th style="width:70px">action</th><th>filename</th>
  <th style="width:10px">type</th><th style="width:50px; text-align: right">Kb</th>
  <th style="width: 140px">&nbsp;&nbsp;date/time</th><th style="width:20px">mode</th>
  </tr>
<%
for i,f in enumerate(files):
    stats=os.stat(os.path.join(path,f))
    mtime=time.localtime(stats.st_mtime)
    mmode=stats.st_mode & 07777
    mtype=mimetypes.guess_type(f)
    if mtype:
        mtype=mtype[0] or ""
    if mtype.startswith("image"):  icon = "picture.gif"
    elif mtype.startswith("text"): icon = "text.gif"
    elif mtype.startswith("audio"): icon = "sound.gif"
    elif mtype.startswith("video"): icon = "movie.gif"
    elif mtype.startswith("application/x-sh"): icon = "script.gif"
    else:                          icon = "unknown.gif"
    
    editable = mtype.startswith("text") or mtype.startswith("application/x-sh")
    \%>
<tr>
  <td>
   <a href="action?a=del&amp;i=<%=i%>" title="delete"><img title="delete" alt="D" src="img/trash.gif" /></a>
   <a href="action?a=ren&amp;i=<%=i%>" title="rename"><img title="rename" alt="R" src="img/rename.gif" /></a>
   <a href="action?a=cpy&amp;i=<%=i%>" title="copy"><img title="copy" alt="C" src="img/copy.gif" /></a>
   <%if editable:%><a href="action?a=edt&amp;i=<%=i%>" title="edit"><img title="edit" alt="E" src="img/edit.gif" /></a><%end%>
   </td>
  <td><a title="download" href="download?i=<%=i%>"><%=self.escape(f)%></a></td>
  <td style="text-align: center"><img src="<%=self.URLprefix%>img/<%=icon%>" alt="" /></td>
  <td style="text-align: right"><%=int(math.ceil(stats.st_size/1024.0))%></td><td><%=time.strftime("%Y-%m-%d . %H:%M:%S",mtime)%></td>
  <td><a href="action?a=chmod&amp;i=<%=i%>" title="change"><%="%03o" % mmode%></a></td>
</tr>
  <%end%>
  </table>
<%end%>
<br />

</div>
