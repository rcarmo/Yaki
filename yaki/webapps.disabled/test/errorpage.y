<%@session=no%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html><head><title>Custom error page</title></head>
<body style="background-color: #500000; color: #ffff80">
<h2>There was a problem with your page.</h2>
<p>
<img src="<%=url('img/ren.gif')%>" style="float: right" alt="shocked Ren">
<em>That's why you see this custom error page ;-)</em>
<h3>Page &quot;<%=self.RequestCtx.Exception_page%>&quot; caused an error: <%=self.RequestCtx.Exception%> (type=<%=self.RequestCtx.Exception_type%>)</h3>
<H3>Traceback (innermost last):</H3>
<%
	import traceback
	list = traceback.format_tb(self.RequestCtx.Exception_tb) + traceback.format_exception_only(self.RequestCtx.Exception_type, self.RequestCtx.Exception_value)
%>
<pre>
<%=self.escape("".join(list[:-1]))%>
<strong><%=self.escape(list[-1])%></strong>
</pre>
<hr>
<address>You can make your error page more interesting than this, of course, if you like.</address>
</body></html>
