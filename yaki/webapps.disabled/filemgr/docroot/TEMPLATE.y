<%!--=========================================

    TEMPLATE for all of the site's pages.

============================================--%>
<%@inputencoding="iso-8859-1"%>
<%@import=import time, filemgr%>
<%
starttime=time.time()

# Contenttype header selector
# For XHTML the "best" would be to send "application/xhtml+xml" to conforming browsers,
# such as Opera and Firefox (they send that in their Accept: header). 
# However it causes Firefox to use a true XML parser to render the page,
# and that results in very strange errors when the page xhtml is not correct due to errors... :(
# So for the time being, we serve the XHTML 1.0 page as "text/html"...
# 
# accept=self.Request.getHeader("Accept") or ""
# if "application/xhtml+xml" in accept:
#     self.setContentType("application/xhtml+xml")
#     trueXHTML=True
# else:
#     self.setContentType("text/html")
#     trueXHTML=False
#
trueXHTML=False

if trueXHTML: self.write('<?xml version="1.0" encoding="utf-8"?>\n')%>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<link rel="stylesheet" type="text/css" href="<%=self.URLprefix%>css/simple.css" />
<!--[if IE]><style>
 div.page {  height: 100%;  /* fix IE-display bug */    }
</style><![endif]-->
<link rel="stylesheet" type="text/css" href="<%=self.URLprefix%>css/theme.css" />
<link rel="stylesheet" type="text/css" href="<%=self.URLprefix%>css/colors.css" />
<%if self.User:%>
<title>File Manager - <%=self.escape(self.User.userid)%></title>
<%else:%>
<title>File Manager</title>
<%end%>
    <script type="text/javascript" src="<%=self.URLprefix%>setfocus.js"></script>
  </head>
<%if self.PageArgs.get("nofocus",""):%><body><%else:%><body onload="setFocus();"><%end%>
    <div class="page">
    <div class="heading"><h1>File Manager</h1>
<%if self.User:%>
Logged in: <strong><%=self.escape(self.User.userid)%></strong>
 <%if getattr(self.SessionCtx,"from_other",False) or self.Request.getSession().shared:%>
 (<a href="<%=self.SessionCtx.filemgr_return_url%>">LEAVE FILEMGR</a>)
 <%else:%>
 (<a href="<%=self.URLprefix%>login.y?logout">LOG OUT</a>)
 <%end%>
<%end%>
&nbsp; &bull; &nbsp; <%=self.Request.getRealServerName()%> 
&nbsp; &bull; &nbsp; <span class="time"><%=time.ctime()%></span>
<%if self.SessionCtx and self.User and not self.SessionCtx.from_other:%>
  <%!-- don't show the filesys location when linked from Frog or another webapp --%>
<br/><span class="light">Filesystem root location: <%=self.escape(self.User.directory)%></span>
<%end%>
</div>
<%$insertpagebody%>
      <div class="footer">File Manager <%=filemgr.VERSION%> - <a href="<%=self.URLprefix%>about">about</a> - valid XHTML+CSS</div>
</div>
<%!-- ============== PAGE TIMINGS ============== --%>
<%
    pagetime = (time.time()-starttime)
    requesttime= (time.time() - self.Request.server.startTimeReal)
    cputime=(time.clock() - self.Request.server.startTimeCPU)
    pagestatus="Process times: page=%0.03f request=%0.03f cpu=%0.03f" % (pagetime, requesttime, cputime)
%>
<div class="pagestatus"><%=pagestatus%></div>
</body>
</html>
