#############################################################################
#
#	$Id: snakelet.py,v 1.74 2008/10/12 17:03:16 irmen Exp $
#	Snakelet implementation
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import urllib, cgi, types, time, weakref
import httpauth
from util import ContextContainer

#
#   The Snakelet base class.
#
#   NOTICE: a Snakelet object (instance) is only created ONCE and will
#   be called concurrently for each request that needs it.
#   So your code must be thread safe. You must be VERY careful to
#   modify global state of the Snakelet (such as attributes, or the
#   snakelet Context).
#
class Snakelet(object):

    SESSION_NOT_NEEDED      = 0     # no session and session cookie (ypage: 'no')
    SESSION_WANTED          = 1     # adds session (and session cookie) (ypage: 'yes')
    SESSION_REQUIRED        = 2     # requires a synchronised session (ypage: 'valid')
    SESSION_LOGIN_REQUIRED  = 3     # requires a session with a logged in user (ypage: 'user')
    SESSION_DONTCREATE      = 4     # if a session exists, use that, otherwise DON'T create a new one (ypage: 'dontcreate')
    
    def __init__(self, url, webappref):
        # avoid circular ref, store only a weakref to our containing webapp.
        if type(webappref) != weakref.ReferenceType:
            raise TypeError("webapp arg for snakelet must be a weakref")
        self._webappref=webappref
        urlprefix=self._webappref().getURLprefix()
        self.urlpattern = urllib.basejoin(urlprefix,url)
        self.snakeletctx = ContextContainer()
        self.content_type="text/html"
        self.errorpage=None
        self.__mtime__=time.time()

    def init(self):
        # initialize snakelet. Override this in subclasses. Called when webapp has completed its initalisation.
        pass

    def getDescription(self):
        # override in subclass for meaningful string.
        return "-"

    def getAuthorizedRoles(self):
        return None
    def getAuthMethod(self):
        return None
                
    def getContext(self):
        return self.snakeletctx
    def getAppContext(self):
        return self.getWebApp().getContext()

    def getFullURL(self):
        (vhost,port) = self.getWebApp().getVirtualHost()
        base = 'http://'+vhost
        if port and port!=80:
            base+=':%d' % port
        return base+self.urlpattern

    def getURL(self):
        return self.urlpattern
    def getWebApp(self):
        return self._webappref()

    def requiresSession(self):
        return self.SESSION_WANTED      # by default, all snakelets are in a session.
    def allowCaching(self):
        return False            # by default, snakelet pages contain "don't cache this" headers
    def getMTime(self):
        return self.__mtime__
        
    def redirect(self, URL, request, response):
        URL = urllib.basejoin(self.urlpattern, URL)  # make always absolute...
        if response.header_written or response.redirection_performed:
            del request,response
            raise RuntimeError('can not redirect twice or when getOutput() has been called')
        request.server.redirect(URL, request, response)

    def include(self, URL, request, response):
        URL = urllib.basejoin(self.urlpattern, URL) # make always absolute...
        return request.server.include(URL, request, response)

    def getErrorPage(self):
        return self.errorpage
    def setErrorPage(self,page):
        self.errorpage=page

    def HTTPauthenticate(self, *vargs, **kwargs):
        return httpauth.HTTPauthenticate(*vargs, **kwargs)
    
    def escape(self,string):
        if string:
            if type(string) in types.StringTypes:
                return cgi.escape(string,True) # force " --> &quot;
            else:
                raise TypeError('must be string argument')
        else:
            return ""
            
    def urlescape(self, url):               # make a url component string url-safe
        return urllib.quote_plus(url)
    def urlunescape(self, url):             # undo url-escaping
        return urllib.unquote_plus(url)

    # def serve(self, request, response): ...    you must implement this in the subclass.
