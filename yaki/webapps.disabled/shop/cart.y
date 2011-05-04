<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head>
<title>Shop</title>
</head>
<body>
<h3>This is in your shopping cart</h3>
<hr>
<p>
<%for (amount, product, price) in self.SessionCtx.cart.getContentLines():
	self.write(amount+' *'+product+' = $'+price+'<br>')
%>	
<strong>Total: $<%=self.SessionCtx.cart.getTotal()%></strong>
<hr>
<p>
<a href="shop.sn?catalog">Back to shop.</a>
<br><a href="shop.sn?emptycart">Empty your shopping cart.</a>
<br><a href="checkout.y">Proceed to checkout.</a>
</body>
</html>
