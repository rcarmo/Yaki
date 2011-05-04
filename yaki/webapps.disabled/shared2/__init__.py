# configuration for this webapp

from snakeserver.user import LoginUser

name="Shared Session webapp 2"
docroot="."
sharedSession=True 
# sharedSessionTLD="charon.local"
sessionTimeoutSecs=40

snakelets={}

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
    pass
