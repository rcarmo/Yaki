# configuration for this webapp

import tsnakelets.testcookie
import tsnakelets.test
import tsnakelets.form
import tsnakelets.snoop

from snakeserver.user import LoginUser

def dirListAllower(path):
	return True	# for test purposes: allow all paths (including snakelet source directory)
def documentAllower(path):
	return True # for test purposes: allow all documents (including Python source files)

name="Test Web application"
docroot="."
assetLocation="img"
sessionTimeoutSecs=60
sessionTimeoutPage="timeout.html"

# indexPages = ["index.y", "index.html", "index.htm"]
#defaultOutputEncoding="UTF-8"
#defaultContentType="text/html"

# defaultErrorPage="errorpage.y"   # set a global error page


snakelets= {
	"cookie.sn": tsnakelets.testcookie.TestCookie,
	"snoop.sn": tsnakelets.snoop.Snoop,
	"memory.sn": tsnakelets.test.Memory,
	"redirect.sn": tsnakelets.test.Redirecter,
	"encoding.sn": tsnakelets.test.Encoding,
	"error.sn": tsnakelets.test.Error,
	"included.sn": tsnakelets.test.Included,
	"utf8form/formaccepter.sn": tsnakelets.form.FormAccepter,
	"utf8form/utf8formaccepter.sn": tsnakelets.form.UTF8FormAccepter,
	"auth/mgmt/httpauth.sn": tsnakelets.test.HTTPAuthenticator_management,
	"auth/bo/httpauth.sn": tsnakelets.test.HTTPAuthenticator_backoffice,
	"doc/*.pdf": tsnakelets.snoop.Snoop,
	"fake/index.sn": tsnakelets.test.FakeIndex,    # fake index page 
	"index.sn": tsnakelets.test.FakeIndex,      # fake index page in webapp root
	}

configItems = {
	"maxPOSTsize":  400000,
	}

authorizationPatterns={
    "authpattern.y": ["admin"],
    "tstauth/*": ["admin"]
 }


def authorizeUser(authmethod, url, username, password, request):
    #  hard-coded users with their passwords and roles
    passwords = { "mike": "apples",   "janet": "pookie" }       # usually the pw's would be encrypted or hashed
    privileges = { "mike": ["admin","dba"],  "janet": ["secretary"] }
    if username in passwords and passwords[username]==password:
        # as an example, we return a full LoginUser object:
        return LoginUser(username,password,"Full username here",privileges[username])
        # ...but it is also possible to just return the set of privileges:
        # return privileges[username] 
    else:
        return None

def init(webapp):
    print ">> INIT WEBAPP",webapp
    
def close(webapp):
    print ">> CLOSE DOWN WEBAPP",webapp
