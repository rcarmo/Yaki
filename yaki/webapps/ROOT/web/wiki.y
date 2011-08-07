<%@outputencoding="UTF-8"%>
<%@inputencoding="UTF-8"%>
<%@allowcaching=yes%>
<%@pagetemplate="themes/minimal/index.y"%>
<div id="post">
<%=self.Request.getParameter('content','') %>
</div>
<div id="status">
<%=self.Request.getParameter('status','') %>
</div>
