<%@pagetemplate=None%>
<%

if self.Request.getSession():
    # Frog integration (or another webapp) -- also see login.y; it contains the same logic
    o_src=self.Request.getParameter("src")
    o_user=self.Request.getParameter("user")
    o_returnurl=self.Request.getParameter("returnurl")
    if o_src and o_user and o_returnurl:
        user=o_user
        self.RequestCtx.login=user
        self.SessionCtx.from_other=True
        self.SessionCtx.filemgr_return_url=o_returnurl
    else:
        if not hasattr(self.SessionCtx,"from_other"):
            self.SessionCtx.from_other=False
%>
<%$httpredirect="browse"%>
