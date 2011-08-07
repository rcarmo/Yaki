<%!--============================================
    PERFORM AN ACTION.
================================================--%>
<%@pagetemplate=TEMPLATE.y%>
<%
self.Request.setEncoding("UTF-8")
action = self.Request.getParameter("a")
    
if action=="chmod":
    self.Yredirect("action/chmod.y")
elif action=="del":
    self.Yredirect("action/delete.y")
elif action=="ren":
    self.Yredirect("action/rename.y")
elif action=="cpy":
    self.Yredirect("action/copy.y")
elif action=="edt":
    self.RequestCtx.edit=True
    self.Yredirect("editfile.y")
elif action=="D_del":
    self.Yredirect("action/delete.y")
elif action=="D_ren":
    self.Yredirect("action/rename.y")
else:
    self.abort("invalid action")

%>
