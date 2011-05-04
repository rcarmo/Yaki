# configuration for this webapp

from filemgr.users import FileUser
import filemgr.snakelets
import os

import logging
log=logging.getLogger("Snakelets.logger")

name="File Manager"
docroot="docroot"
sessionTimeoutSecs=30*60     # 30 minutes
sharedSession=False          # set to True, then also set Frog's one to True --> single signon

defaultOutputEncoding="UTF-8"


# The required privilege is "filemgr_access";
# this is set in the special filemgr user object (filemgr/users.py)
authorizationPatterns={ 
    "*": ["filemgr_access"],   
    "login.y": None,
    "cookiecheck.y": None,
    "about": None,
    "*.css": None,
    "*.js": None
}

def documentAllower(path):
    return True  # allow all (even .py files)

authenticationMethod = ("loginpage", "login.y")

snakelets= { 
    "download" : filemgr.snakelets.DownloadFile
}

configItems = {

    # The authorised users.
    # Use the 'mkuser.py' script to help adding new users.
    # (if you use frog and SharedAuth, you can leave this... it will use Frog's userbase)
    "knownusers" : {
        "rcarmo": FileUser("rcarmo", "Rui Carmo", r"/Users/rcarmo", passwordhash="0e4e429dbb308001663177fbbabfb186f6b73781"),  # XXX set this to correct values
    },
    
}


#
#   USER AUTHORIZATION 
#
def authorizeUser(authmethod, url, username, password, request):
    # try to use shared auth (used with Frog webapp)
    try:
        sharedauth=request.getWebApp().server.getPlugin("SharedAuth")
        result=sharedauth.authorizeUser(authmethod, url, username, password, request)
        if result:
            # auth success!
            # but, FileMgr requires FileUser objects instead of regular LoginUser objects,
            # so we have to convert it. The directory is set by the other auth method.
            return FileUser(result.userid, result.name, result.directory, result.password.encode("hex"))
    except KeyError:
        # no shared auth available
        pass
    # no shared auth available, or shared auth failed. 
    if username in configItems["knownusers"]:
        user = configItems["knownusers"][username]
        if user.checkPassword(password):
            return user
    return None


#
#   WEBAPP INIT
#
def init(webapp):
    import snakeserver.server
    version=snakeserver.server.SNAKELETS_VERSION.split()[1]
    if version.lower().endswith("cvs"):
        version=version[:-3]
    if float(version)<1.42:
        msg="FileMgr requires Snakelets version 1.42 or newer"
        print "ERROR:",msg
        raise RuntimeError(msg)
    os.umask(0077) # protect written files, only readably by current user.
    import mimetypes
    mimetypes.types_map[".java"]="text/x-java-source"
    mimetypes.types_map[".log"]="text/x-logfile"
    mimetypes.types_map[".conf"]="text/x-configfile"
    mimetypes.types_map[".sh"]="text/x-shell-script"

    
def close(webapp):
    pass

