<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<%
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
<h2>Checkout</h2>
<h3>This is in your shopping cart</h3>
<hr>
<p>
<%for (amount, product, price) in self.SessionCtx.cart.getContentLines():
	self.write(amount+' * '+product+' = $'+price+'<br>')
%>	
<strong>Total: $<%=self.SessionCtx.cart.getTotal()%></strong>
<hr>
<p>
<a href="shop.sn?catalog">Shop for more items.</a>
<br><a href="shop.sn?emptycart">Cancel your purchase.</a>
<p>
<!-- This must be solved better -->
<%if self.SessionCtx.cart.getTotal()==0:
	self.write("You don't have anything to buy!")
	self.abort("empty cart")%>

If you are satisfied, please fill in the details below and submit your shopping order.
<form method="post" action="shop.sn?commit">
<table summary="customer info">
<tr>
<td>Your name
<td><input type="text" name="name">
</tr>
<tr>
<td>Credit card number
<td><input type="text" name="card">
</tr>
<tr><td></td></tr>
<tr>
<td>&nbsp;
<td><%=message%>
</tr>
<tr>
<td>&nbsp;
<td><input type="submit" value="Submit order" name="submit">
</tr>
<tr>
<td>&nbsp;
<td><sub>Note that this is just an example, your data will not be stored or processed</sub>
</tr>
</table>
</form>
</body>
</html>
