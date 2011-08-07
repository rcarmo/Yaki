<%@outputencoding="UTF-8"%>
<%
import sys, traceback
template = self.ApplicationCtx.templates['error-page']
try:
  type = self.RequestCtx.Exception_type
  list = traceback.format_tb(self.RequestCtx.Exception_tb) + traceback.format_exception_only(self.RequestCtx.Exception_type, self.RequestCtx.Exception_value)
  traceback = u"<pre>%s<strong>%s</strong></pre>" % (self.escape(u"".join(list[:-1])),self.escape(list[-1]))
  if 'yaki.Engine.Starting' in str(type):
    buffer = template % { 'code': 503, 
                          'meta': '<meta http-equiv="REFRESH" content="10;">',
                          'path': self.RequestCtx.Exception_page, 
                          'heading': "Don't Panic!",
                          'hostname' : self.Request.getServerName(),
                          'message' : 'The server is (re)starting...',
                          'explanation' : u"""
                          <script type="text/javascript">
                          $(document).ready(function() {
                            setTimeout( "location.reload()", 10000 );
                          });
                          </script>
                          <img align="right" src="/img/spinner_black.gif">
                          <p>The application server managing this site is being restarted.</p>
                          <p>Please wait, this page will auto-refresh in 10 seconds...</p>"""}
  else:
    buffer = template % { 'code': 500, 
                          'meta': '<meta http-equiv="REFRESH" content="30;">',
                          'heading': "There was a disturbance in the Force",
                          'path': self.RequestCtx.Exception_page, 
                          'hostname' : self.Request.getServerName(),
                          'message' : self.RequestCtx.Exception,
                          'explanation' : u"<h4>%s</h4>%s" % (type,traceback) }
except Exception, detail:
  cla, exc, trbk = sys.exc_info()
  buffer = template % { 'code': 503,
                        'meta': '',
                        'heading': "Oops!",
                        'path': self.Request.getRequestURL(), 
                        'hostname' : 'localhost',
                        'message' : cla.__name__,
                        'explanation' : "%s" % detail}
  pass
%>
<%=buffer%>
