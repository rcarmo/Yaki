#############################################################################
#
#	$Id: websession.py,v 1.25 2008/10/12 15:42:16 irmen Exp $
#	HTTP session management
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

from util import ContextContainer
import time
import weakref, threading
from user import LoginUser
import logging


log=logging.getLogger("Snakelets.logger")


class SecurityError(Exception):
    def __init__(self, value, extrainfo=None):
        Exception.__init__(self, value)
        if extrainfo:
            self.Snakelets_extrainfo = extrainfo
        
class SessionAddressError(SecurityError): pass


#
#   The SESSION manager.
#   Every webapp has an instance of this thing,
#   it manages the collection of active sessions.
#

class SessionManager(dict):
    def __init__(self, webappref):
        self.webappref=webappref
    def __setitem__(self, key, value):
        dict.__setitem__(self,key,value)
    def __getitem__(self, key):
        return dict.__getitem__(self,key)
    def __delitem__(self, key):
        dict.__delitem__(self,key)
    def clear(self):
        dict.clear(self)
    def scanSessionTimeouts(self):
        for session in self.values()[:]:
            session.destroyIfOverAged()


#
#   The SESSION object itself. Access point for all session-related stuff.
#   It is associated with each request (if the request is part of a session).
#
class Session(object):
    def __init__(self, sessid, timeoutsecs, remoteAddr, webappref):
        self.sessionID=sessid
        self.context=ContextContainer() # session context
        self.timeoutsecs=timeoutsecs
        self.touch()
        self.new=True   # set this *after* the touch()
        self.timeout=False  # will be True if a session timeout was detected
        self.user=None
        self.createtime=time.time()
        if type(webappref) != weakref.ReferenceType:
            raise TypeError("webapp for session must be a weakref")
        self.webappref=webappref
        self.shared=webappref().sharedSession
        self.remoteAddr=remoteAddr
        self.lock=threading.Lock()
    def setRequestData(self, request, response):
        # being set on each new request
        if self.remoteAddr != str(request.getRealRemoteAddr()):
            log.warn("SECURITY WARNING: attempt to transport session to a different remote address")
            log.warn( "From: %s  to: %s" % (self.remoteAddr, request.getRealRemoteAddr() ))
            # NOTICE: this used to be a security ERROR, but this causes problems
            #         when the user is behind a proxy that changes IP addresses..
            # new,old = request.getRealRemoteAddr(), self.remoteAddr
            # del request, response
            # raise SessionAddressError("attempt to transport session to a different remote address",
            #        "The last request accessing your session information came from a different IP address (%s) than before (%s). "
            #        "This is a security error, to prevent somebody else from stealing your data," % (new, old))
        self.requestref=weakref.ref(request)
        self.responseref=weakref.ref(response)
    def getID(self):
        return self.sessionID
    def isNew(self):
        return self.new
    def getLoggedInUser(self):
        return self.user
    def loginUser(self, user):
        if not isinstance(user, LoginUser):
            raise TypeError("user must be a snakelet LoginUser instance")
        self.user=user
    def logoutUser(self):
        self.user=None
    def getContext(self):
        return self.context
    def getRemoteAddr(self):
        return self.remoteAddr
    def touch(self):
        # called by server - don't call yourself
        self.lastused=time.time()
        self.new=False
        self.timeout=False
    def isOverAged(self):
        return (time.time()-self.lastused)>self.timeoutsecs
    def destroy(self, external=False):
        # notification for objects on session
        self.lock.acquire()
        try:
            request=self.requestref()
            if not external and self.webappref():
                self.webappref()._deleteSession(self, self.responseref())
            self.logoutUser()
            if request:
                # This session still belongs to a request. Clear it from the request.
                request.setSession(None)
        finally:
            self.lock.release()
    def destroyIfOverAged(self):
        if self.isOverAged():
            self.destroy()
