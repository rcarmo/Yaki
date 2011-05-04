# configuration for this webapp

import account
from snakeserver.user import LoginUser

name="Test Account/Login"
docroot="."
authenticationMethod = ("loginpage","login.y")
defaultRequestEncoding = "UTF-8"

snakelets= {
	"account.sn": account.Account
	}
	
configItems = {
    # the pre-defined users, also any new users are added in this datastructure:
    "users": { "test": LoginUser("test","test","Test User") }       
}

# This is the standard way of authenticating users;
# this function will be called by snakelets if you need to tell
# it if a given user is authorized or not.
def authorizeUser(authmethod, url, username, password, request):
    if username in configItems["users"]:
        user = configItems["users"][username]
        if user.checkPassword(password):
            return user      # you can also just return a set of privileges for this user
    return None
    
#def init(self):
#    print 1/0