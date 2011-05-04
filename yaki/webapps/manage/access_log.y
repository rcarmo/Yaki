<%!--
   Access.log scanner
   Based on a contribution by Vincent Delft
--%>
<%@pagetemplate="manage_template.y"%>
<%@pagetemplatearg=title=Server Statistics%>
<%@import=import access_log,os.path,time,urllib%>
<div class="panel">
<form method="post" action="<%=self.getURL()%>">
<%
r=access_log.AccessLog()
r.parse(os.path.normpath(os.path.join(self.WebApp.getFileSystemPath(),'../../logs/access.log')))
r.analyzer()
datel=r.getDateOrdered()
%>
<p>Filter: <select name="filter" OnChange="submit()">
 <option value="all">No filter</option>
<%
selected=self.Request.getParameter("filter","extension")
for param in r.getParameters():
   if param==selected:
       self.write("""<option value="%s" selected>%s</option>""" % (param,param))
   else:
       self.write("""<option value="%s">%s</option>""" % (param,param))
if selected=="all":
    datalist=r.getParameters()
else:
    datalist=[selected]
self.SessionCtx.analyzer=r
%>
</select>
</form>
<table summary="access log info">
<%for date in datel:%>
<tr><th colspan="3" align="left"><h3>Server stats for <%=date%>&nbsp;&nbsp; (KB sent: ~<%=r.bytessent[date]/1024%>)</h3></th></tr>
 <%for key in datalist:%>
  <%
   items,total,maxw=r.getStats(date,key)
   maxw_pixels=200
   ratio=maxw_pixels*1.0/maxw
  %>
  <tr class="actions"><td colspan="3"><b><%=key%></b>&nbsp; <%='Items:%s, Total:%s' % (items,total)%></td></tr>
  <%for count,data in r.getOrderedValues(date,key):%>
   <tr>
     <td style="width: <%=maxw_pixels%>px; max-width: <%=maxw_pixels%>px;"><img src="bar.gif" height="13" width="<%=count*ratio%>" alt="<%=count%>"></td>
     <td style="width: 6em; font-size: 80%"><%=count%></td>
     <td style="width: 30em; font-size: 80%; white-space: normal;"><a href="access_disp?date=<%=date%>&amp;key=<%=key%>&amp;data=<%=urllib.quote_plus(data)%>"><%=data%></a></td>
   </tr>
  <%end%>
 <%end%>
<%end%>
</table>

</div>

