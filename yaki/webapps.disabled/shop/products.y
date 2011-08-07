<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%products=self.ApplicationCtx.products
if hasattr(self.RequestCtx,'message'):
	message=self.RequestCtx.message
else:
	message=''
%>

<html>
<head>
<title>Shop</title>
</head>
<body>
<h3>Welcome to the Shop Example.</h3>
<h1>Available products</h1>
<form name="shop" action="shop.sn?catalog" method="post">
<p>
<%for id in products.keys():
	(product, price) = products[id]
	self.write('<input type="submit" name="buy'+str(id)+'" value="buy"> '+
		'<input type="text" size="2" value="1" name="amount'+str(id)+'">'+product+', $'+str(price)+'<br>')
%>	
</form>
<p><%=message%>
<p><a href="cart.y">See your shopping cart.</a>
<br><a href="checkout.y">Proceed to checkout.</a>
</body>
</html>
