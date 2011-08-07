<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%products=self.ApplicationCtx.products
name='John Doe'
card='9999-9999'
total=0
if hasattr(self.RequestCtx,'name'):
	name=self.RequestCtx.name
if hasattr(self.RequestCtx,'card'):
	card=self.RequestCtx.card
if hasattr(self.RequestCtx,'total'):
	total=self.RequestCtx.total
%>

<html>
<head>
<title>Shop</title>
</head>
<body>
<h2>Thank you for shopping with us.</h2>
<p>
<%=name%>, your credit card <%=card%> will be charged with
the total amount of your purchase; $<%=total%>.
<p>Please shop with us again.
<p><a href="index.html">Back to shop.</a>
<p>
<sub>This is just an example, nothing is stored or will actually be charged.</sub>
<%
self.Request.getSession().destroy()
%>
<br><sub>Your session and shopping cart have been cleared.</sub>
</body>
</html>
