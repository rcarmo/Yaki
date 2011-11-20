<%@outputencoding="utf-8"%>
<%@inputencoding="utf-8"%>
<%@gobblews=no%>
<%
c = self.ApplicationCtx.cache;
c.purge()
%>
Application cache purged.
<%
# This issues a request to Varnish and asks it to purge/ban the content from its internal cache (requires specific handling in VCL, of course)
#import httplib
#connection =  httplib.HTTPConnection('127.0.0.1:80')
#body_content = 'X-Purge-Regex: .*'
#connection.request('PURGE', '/', body_content)
#result = connection.getresponse().read()
%>
