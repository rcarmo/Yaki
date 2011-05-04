import cgi,os,sys,time
import types

from snakeserver.snakelet import Snakelet
from snakeserver.user import LoginUser



class Account(Snakelet):

	def init(self):
	    pass

	def getDescription(self):
		return "Handles login and accounts"

	def serve(self, request, response):
        # you can set the form encoding per page: request.setEncoding("UTF-8")
        #... but this webapp has defined a global defaultRequestEncoding in the webapp init file.

		form = request.getForm()
		action = form.get("action")
		if action=="create":
			# called from the create account page
			self.prefillFormValues(form, request.getContext())
			name=form.get('name','')
			login=form.get('login','')
			passw1=form.get('password1','')
			passw2=form.get('password2','')
			if len(name)<3:
				request.getContext().fieldErrors["name"]='Name must be at least 3 letters.'
				name=''
			if len(login)<4:
				request.getContext().fieldErrors["login"]='Login must be at least 4 letters.'
			if len(passw1)<4:
				request.getContext().fieldErrors["password1"]='Password must be at least 4 characters.'
			elif passw1!=passw2:
				request.getContext().fieldErrors["password2"]='Passwords do not match.'
			if request.getContext().fieldErrors:
				# go back to input form.
				self.redirect('createprofile.y',request,response)
			else:
				rctx=request.getContext()
				users = self.getWebApp().getConfigItem("users")
				if login in users:
					request.getContext().fieldErrors["login"]='That login ID is already in use.'
					self.redirect('createprofile.y',request,response)
				else:
					# store new account and proceed to confirmation.
					users[login]=LoginUser(login,passw1,name)
					rctx.name=name
					rctx.login=login
					self.redirect('profilecreated.y',request,response)

		elif action=="update":
			self.prefillFormValues(form, request.getContext())
			name=form.get('name',"")
			passwd=form.get('password_old',"")
			newpass1=form.get('password_new1',"")
			newpass2=form.get('password_new2',"")
			if len(name)<3:
				request.getContext().fieldErrors["name"]="Name must be at least 3 letters."
				name=''
			if newpass1 and len(newpass1)<4:
				request.getContext().fieldErrors["password_new1"]="Password must be at least 4 characters."
			elif newpass1!=newpass2:
				request.getContext().fieldErrors["password_new2"]="Passwords didn't match."
			if newpass1 and not request.getSession().getLoggedInUser().checkPassword(passwd):
				request.getContext().fieldErrors["password_old"]="Original password incorrect."
			if request.getContext().fieldErrors:
				# go back to the form, to correct the errors.
				self.redirect('viewprofile.y',request,response)
			else:
				# update the current user's profile
				request.getSession().getLoggedInUser().name=name
				if newpass1:
					request.getSession().getLoggedInUser().password=newpass1
				self.clearFormValues(request.getContext())
				self.redirect('loggedin.y',request,response)

        # notice that the "login" action is not done here, but in the login.y page itself
        
		else:
			response.sendError(501,"invalid action")

	def prefillFormValues(self, form, requestCtx):
		fieldValues={}
		for key in form.keys():
			value=form[key]
			if type(value) in types.StringTypes:
				fieldValues[key]=value
		requestCtx.fieldValues=fieldValues
		requestCtx.fieldErrors={}
	def clearFormValues(self, requestCtx):
		requestCtx.fieldValues={}
		requestCtx.fieldErrors={}
