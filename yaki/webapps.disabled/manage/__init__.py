# configuration for this webapp

import manager
from snakeserver.user import LoginUser

name="Server Management"
docroot="."

sessionTimeoutSecs=1800   # 30 minuten

authorizationPatterns = {
	"login.y":	None,
	"login": None,
	"index.html": None,
	"*.css": None,
	"*":	["admin"]
	}

authenticationMethod = ("loginpage","login.y")

def authorizeUser(authmethod, url, username, password, request):
    users = {
        "test": LoginUser("test", "test", "Test Admin", ["admin"])   # XXX hardcoded test user
        }
    
    if username in users and users[username].checkPassword(password):
        return users[username]      # could also just return a set/list of privileges
    else:
        return None

snakelets= {
	"manage.sn": manager.Manager
	}
	

configItems = {
}


#def init(webapp):
#    print "Management init!!",webapp
    
#def close(webapp):
#    print "Management close!!",webapp
