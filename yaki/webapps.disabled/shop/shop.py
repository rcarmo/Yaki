import cgi,os,sys,time

from snakeserver.snakelet import Snakelet


class ShoppingCart:
	def __init__(self):
		self.contents=[]
		pass
	def buy(self, product, price, amount):
		self.contents.append((product,price,amount))
	def empty(self):
		self.contents=[]
	def size(self):
		return reduce(lambda total,(prod,price,amnt): total+amnt, self.contents, 0)
	def getContentLines(self):
		lines=[]
		for c in self.contents:
			lines.append((str(c[2]),c[0],str(c[2]*c[1])))
		return lines	
	def getTotal(self):
		return reduce(lambda total,(prod,price,amnt): total+price*amnt, self.contents, 0)
		

class Shop(Snakelet):
	def init(self):
		self.getAppContext().products= {
			1001: ('Television', 499.95),
			1020: ('Fridge', 280.00),
			1030: ('Vacuum cleaner', 47.50),
			1040: ('CD player', 99.90) }

	def getDescription(self):
		return "Shop, handles storage and selling"

	def serve(self, request, response):
		if hasattr(request.getSessionContext(),"cart"):
			cart=request.getSessionContext().cart
			print "Got existing shoppingcart"
		else:
			cart=ShoppingCart()
			request.getSessionContext().cart=cart
			print "--> NEW SHOPPINGCART"
		arg=request.getArg()
		if arg=='catalog':
			request.getContext().message='Welcome. Select products to buy.'
			form = request.getForm()
			for key in form.keys():
				if key[:3]=='buy':
					id=int(key[3:])
					product=self.getAppContext().products[id]
					amount=int(form.get('amount'+str(id),'1'))
					cart.buy(product[0],product[1],amount)
					request.getContext().message='You bought '+str(amount)+' '+product[0]+'(s), total cost $'+str(amount*product[1])
					request.getContext().message+='<br>Select more products to buy.'
			request.getContext().message+="<p>There are %d products in your shopping cart." % cart.size()
			self.redirect('products.y',request,response)
		elif arg=='emptycart':
			cart.empty() 
			request.getContext().message='Your shopping cart has been emptied.'
			self.redirect('products.y',request,response)
		elif arg=='commit':
			form=request.getForm()
			name=form.get('name')
			card=form.get('card')
			if not name or not card:
				request.getContext().message='Please fill in your name and your card number.'
				self.redirect('checkout.y',request,response)
				return
			total=cart.getTotal()
			request.getContext().name=name
			request.getContext().card=card
			request.getContext().total=total
			self.redirect('exit.y',request,response)
		#else:
		#	response.sendError(404,"invalid shop command")


