#############################################################################
#
#	$Id: webapp.py,v 1.172 2008/10/12 17:03:16 irmen Exp $
#	Web Application logic
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import os, urllib, urlparse, cStringIO, cgi, gzip, zlib
import time, hashlib, sys, random, types, weakref, inspect
import binascii, fnmatch
import snakelet, httpauth
from threading import Lock
from YpageEngine import YpageEngine, Ypage
from ypage.compiler import CompilerError
from mycookie import SESSION_COOKIE_NAME
from mycookie import SESSION_COOKIE_NAME_SHARED
import request_response
import websession
from user import LoginUser
import logging
import traceback

log=logging.getLogger("Snakelets.logger")

MAX_SESSIONS_PER_IP = 500       # the max. number of open sessions that Snakelets allows for a single IP address


class NotHandled(Exception):
    pass
class TimeoutPageNotFound(NotHandled):
    def __init__(self, cookie=None):
        self.cookie=cookie
class TooManySessions(Exception):
    pass
class WebAppInitialisationError(Exception):
    pass
class AbortPage(Exception):
    pass

class WebAppContext(object):
    # storage container for the web app context.
    def __init__(self, webapp):
        # initialize initial context values.
        self.AbsPath=unicode(webapp.getFileSystemPath())
        self.Name=unicode(webapp.getName())
        self.UrlPrefix=unicode(webapp.getURLprefix())


class WebAppConfigError(Exception): pass


#
# Factory function that reads the webapp config
# and creates an appropriate webapp object.
#
def createWebApp(abspath, webapp_path, urlprefix, virtualHost, server):

    WA=__import__("webapps."+webapp_path, locals())
    WA=getattr(WA,webapp_path)
    webapp=None
    try:
        WA.configItems=getattr(WA,"configItems",{})
        WA.dirListAllower=getattr(WA,"dirListAllower",None)
        WA.documentAllower=getattr(WA,"documentAllower",None)
        WA.defaultOutputEncoding=getattr(WA,"defaultOutputEncoding",None)
        WA.defaultContentType=getattr(WA,"defaultContentType",None)
        WA.defaultPageTemplate=getattr(WA,"defaultPageTemplate",None)
        WA.defaultRequestEncoding=getattr(WA,"defaultRequestEncoding",None)
        WA.defaultErrorPage=getattr(WA,"defaultErrorPage",None)
        WA.sessionTimeoutSecs=getattr(WA,"sessionTimeoutSecs",600) # default=10 minutes
        WA.sessionTimeoutPage=getattr(WA,"sessionTimeoutPage",None)
        WA.sharedSession=getattr(WA,"sharedSession",False)
        WA.sharedSessionTLD=getattr(WA,"sharedSessionTLD",None)
        WA.compileAllPages = server.precompileYPages
        WA.writePageSource = server.writePageSource
        WA.urlprefix = unicode(server.serverURLprefix+urlprefix)
        WA.assetLocation = getattr(WA,"assetLocation",None)

        WA.authorizeUser=getattr(WA,"authorizeUser", None)
        WA.authMethod=getattr(WA,"authenticationMethod", None)
        if WA.authMethod and not WA.authMethod[0] in ("httpdigest", "httpbasic", "loginpage"):
            raise WebAppConfigError("unknown authenticationMethod: "+WA.authMethod[0])
        _authPatterns=getattr(WA,"authorizationPatterns",{})
        _patterns={}
        for (pat, privs) in _authPatterns.items():
            pat=WA.urlprefix+pat.lstrip('/')+'*'   # append *-wildcard to prevent security holes
            if privs is not None:
                if isinstance(privs, (unicode, str)):
                    raise WebAppConfigError("privileges in authorizationPatterns are a str, must be set/sequence")
                if not isinstance(privs, (set,frozenset)):
                    try:
                        privs=frozenset(privs)
                    except TypeError:
                        raise WebAppConfigError("privileges in authorizationPatterns must be set/sequence")
                if not privs:
                    log.warn("empty privilege set, access impossible for url pattern "+pat)
            _patterns[pat]=privs
        WA.authorizationPatterns=_patterns

        WA.initFunc = getattr(WA,"init", None)
        WA.closeFunc = getattr(WA,"close",None)
        ## Allow webapps to set their own array of index pages. Default=server defined list.
        WA.indexPages = getattr(WA, "indexPages", server.INDEXPAGES)

        WA.absFSpath = abspath
        WA.shortname = webapp_path
        WA.virtualHost=virtualHost      # (vhost,vport)
        WA.server = server

        webapp = WebApp(WA)

        if WA.initFunc:
            WA.initFunc(webapp)
        webapp._initSnakelets()


    except Exception ,x:
        log.error("!!! problem during webapp load: "+str(x))
        log.error("!!! webapp="+urlprefix)
        log.error( "".join(traceback.format_exception(*sys.exc_info())) )
        print >>sys.stderr,"ERROR: Failed to load webapp",urlprefix
        print >>sys.stderr,"CAUSE (see log for details):",x
        log.error("Failed to load webapp, closing down")
        if hasattr(WA,"closeFunc") and callable(WA.closeFunc):
            try:
                WA.closeFunc(webapp)
            except Exception,x:
                log.warn("Error during closing: %s",x)
                log.warn( "".join(traceback.format_exception(*sys.exc_info())) )
        raise
    else:
        return webapp


class WebApp(object):
    def __init__(self, WAConfig):
        self.server=WAConfig.server
        self.escrow = WAConfig.server.escrow
        self.configitems=WAConfig.configItems
        self.absFSpath=WAConfig.absFSpath
        self.docrootFSPath=os.path.normpath(os.path.join(self.absFSpath,WAConfig.docroot))
        self.name=(WAConfig.shortname,WAConfig.name)
        self.urlprefix=WAConfig.urlprefix
        if WAConfig.assetLocation:
            if not WAConfig.assetLocation.endswith('/'):
                WAConfig.assetLocation+='/'
            self.assetprefix = unicode(urlparse.urljoin(self.urlprefix,WAConfig.assetLocation))
        else:
            self.assetprefix = None
        self.dirListAllower=WAConfig.dirListAllower or (lambda path: False)    # default=don't allow dir listing
        self.documentAllower=WAConfig.documentAllower or (lambda path: os.path.splitext(path)[1].lower() not in ('.py', '.pyc'))  # default=don't serve python source or bytecode files
        self.virtualHost=WAConfig.virtualHost
        self.enabled=True
        self.authorizationPatterns=WAConfig.authorizationPatterns
        self.authorizeUser=WAConfig.authorizeUser
        self.authMethod=WAConfig.authMethod
        self.startuptime=time.time()
        self.defaultOutputEncoding=WAConfig.defaultOutputEncoding
        self.defaultContentType=WAConfig.defaultContentType
        self.defaultPageTemplate=WAConfig.defaultPageTemplate
        self.defaultErrorPage=WAConfig.defaultErrorPage
        self.defaultRequestEncoding=WAConfig.defaultRequestEncoding
        self.sessionTimeoutSecs=WAConfig.sessionTimeoutSecs
        self.sessionTimeoutPage=WAConfig.sessionTimeoutPage
        self.sharedSessionTLD=WAConfig.sharedSessionTLD
        self.sharedSession=WAConfig.sharedSession
        ## Allow webapps to set their own array of index pages.
        self.indexPages=WAConfig.indexPages
        # create a context for this web application.
        self.context=WebAppContext(self)
        # initialize snakelets
        self.snakelets={}
        for (snk, snakeletClass) in WAConfig.snakelets.items():
            self.snakelets[snk]=snakeletClass(snk,weakref.ref(self))  # create a snakelet instance.

        # session tracking
        self.sessions=websession.SessionManager(weakref.ref(self))

        self.lock = Lock()  # thread lock for session management
        self.pageEngine=YpageEngine(WAConfig.shortname, self.virtualHost[0], WAConfig.writePageSource)
        self.closeFunc = WAConfig.closeFunc

    def _initSnakelets(self):
        # initialise all snakelets, this is done after webapp initialisation
        for snk in self.snakelets:
            self.snakelets[snk].init()

    def close(self):
        self.sessions.clear()
        if self.closeFunc:
            self.closeFunc(self)
            self.closeFunc=None
        del self.server
        del self.snakelets
        del self.pageEngine

    def __str__(self):
        return "[WebApp '%s' on vhost '%s', urlprefix=%s]" % (self.name[1], self.virtualHost[0], self.urlprefix)

    def getFileSystemPath(self):
        return self.absFSpath
    def getDocRootPath(self):
        return self.docrootFSPath
    def getName(self):
        return self.name
    def isEnabled(self):
        return self.enabled
    def setEnabled(self, enabled):
        self.enabled=enabled

    def getVirtualHost(self):       # returs (vhost, vport) tuple
        return self.virtualHost
    def getContext(self):
        return self.context
    def getURLprefix(self):
        return self.urlprefix
    def getAssetprefix(self):
        return self.assetprefix
    def getConfigItems(self):
        return self.configitems
    def getConfigItem(self, item):
        return self.configitems[item]
    def getSnakelets(self):
        return self.snakelets
    def getSnakelet(self, urlpattern):
        return self.snakelets[urlpattern]

    def _getPath(self, handlerpath):
        return handlerpath[len(self.urlprefix):]    # this has no starting slash
    def getFullPath(self, path):
        return os.path.join(self.docrootFSPath,urllib.url2pathname(path))
    def mkAssetUrl(self, path, htmlescape=True):   # assetlink creation method
        if htmlescape:
            return cgi.escape(self.assetprefix+path, True)
        else:
            return self.assetprefix+path
    def mkUrl(self, path, arg="", params=[], htmlescape=True):   # url-creation method that does correct url-escaping
        urlescape=urllib.quote_plus
        if arg:
            arg='?'+urlescape(arg)
            if params:
                arg+='&'
        elif params:
            arg='?'
        url=self.urlprefix+path+arg   # do NOT escape 'path' itself
        if params:
            if isinstance(params,dict):
                params=params.items()
            params = [ "%s=%s" % (urlescape(name),urlescape(val)) for name,val in params ]
            url += "&".join(params)
        if htmlescape:
            return cgi.escape(url, True)
        else:
            return url

    def do_HEAD(self, handler):
        pageprocessor = self.getPageProcessor(self._getPath(handler.path), handler)
        if pageprocessor:
            pageprocessor.do_HEAD()
            handler.end_headers()
        else:
            # look for a webapp that has the same name as the given url (append a slash)
            webapp = self.server.getWebApp(handler.path+'/', handler.virtualhost, False)
            if webapp and webapp is not self:
                handler.redirectToWebappWithSlash(None)
            else:
                if self.checkAuthorizationPatterns(None, None, None, handler):
                    # we received a HEAD request for a URL that is allowed, but that we don't handle.
                    raise NotHandled()

    def do_GET(self, handler, passthroughRequest, passthroughResponse):
        timeout = (passthroughRequest and passthroughRequest.session and passthroughRequest.session.timeout) or False
        pageprocessor = self.getPageProcessor(self._getPath(handler.path), handler)
        if pageprocessor:
            return pageprocessor.do_GET(passthroughRequest, passthroughResponse, timeoutpage=timeout)
        else:
            # look for a webapp that has the same name as the given url (append a slash)
            webapp = self.server.getWebApp(handler.path+'/', handler.virtualhost, False)
            if webapp and webapp is not self:
                return handler.redirectToWebappWithSlash(passthroughResponse)
            else:
                if self.checkAuthorizationPatterns(passthroughRequest, passthroughResponse, None, handler):
                    # we received a GET request for a URL that is allowed, but that we don't handle.
                    if timeout:
                        raise TimeoutPageNotFound(cookie=passthroughResponse.getCookies()[SESSION_COOKIE_NAME])
                    else:
                        raise NotHandled()
        return None

    def do_POST(self, handler):
        # This works without the passthroughRequest/response, because a POST is never used for inclusion/redirection.
        pageprocessor = self.getPageProcessor(self._getPath(handler.path), handler)
        if pageprocessor:
            return pageprocessor.do_POST()
        else:
            # look for a webapp that has the same name as the given url (append a slash)
            webapp = self.server.getWebApp(handler.path+'/', handler.virtualhost, False)
            if webapp and webapp is not self:
                return handler.redirectToWebappWithSlash(passthroughResponse)
            else:
                handler.send_error(501, "POST url is invalid")
                return None


    class PageProcessor(object):
        def __init__(self, webapp, handler, url, pathinfo, args):
            self.webapp=webapp
            self.handler=handler
            self.url=url
            self.pathinfo=pathinfo
            self.args=args
        # a PageProcessor should also implement do_HEAD, do_GET and do_POST

    class SnakeletProcessor(PageProcessor):
        def do_HEAD(self):
            self.webapp.run_snakelet(self.handler, self.url, self.pathinfo, self.args, None, None, True)
        def do_GET(self, passthroughRequest, passthroughResponse, timeoutpage=False):
            # The snakelet code writes to the output stream itself. The return value is always None.
            # Note that in case of a timeout page, the session cookie is nicely replaced.
            return self.webapp.run_snakelet(self.handler, self.url, self.pathinfo, self.args, passthroughRequest, passthroughResponse)
        def do_POST(self):
            # POST is essentially the same as GET (without any passthrough request/response).
            # The snakelet code writes to the output stream in both cases. The return value is always None.
            return self.webapp.run_snakelet(self.handler, self.url, self.pathinfo, self.args)
    class YpageProcessor(PageProcessor):
        def do_HEAD(self):
            self.webapp.run_Ypage(self.handler, self.url, self.pathinfo, self.args, None, None, True)
        def do_GET(self, passthroughRequest, passthroughResponse, timeoutpage=False):
            # An Ypage does NOT write to the output stream itself!
            # It collects its output in a new stream buffer object that is the return value.
            # (the server will take care of writing it to the output stream).
            # Note that in case of a timeout page, the session cookie is nicely replaced.
            return self.webapp.run_Ypage(self.handler, self.url, self.pathinfo, self.args, passthroughRequest, passthroughResponse)
        def do_POST(self):
            # POST is essentially the same as GET (without any passthrough request/response).
            return self.webapp.run_Ypage(self.handler, self.url, self.pathinfo, self.args)
    class StaticProcessor(PageProcessor):
        def do_GET(self, passthroughRequest, passthroughResponse, timeoutpage=False):
            # Note that in case of a timeout page, the session cookie is not automatically replaced,
            # that's why the timeout flag is passed on so that the appropriate http header is generated.
            return self.serveStaticFile(False,passthroughResponse,timeoutpage=timeoutpage)
        def do_HEAD(self):
            self.serveStaticFile(True,None)
        def serveStaticFile(self, headOnly, passthroughResponse, filename=None, headers=None, timeoutpage=False):
            headers=headers or {}
            fspath=filename or self.webapp.getFullPath(self.url)
            f=open(fspath,'rb')   # always read in binary format
            ctype = self.handler.guess_type(fspath)
            stats = os.stat(fspath)
            hdr = self.handler.headers.getheader('accept-encoding')
            compress = False
            if hdr and (hdr.find("gzip") != -1) and  filter(fspath.lower().endswith, ['.css','.js','.xml','.html','.htm','.txt']):
              compress = True
            if not passthroughResponse or not passthroughResponse.used():
                (etag,lmod) = self.webapp.create_ETag_LMod_headers(stats.st_mtime, stats.st_size, stats.st_ino)
                # check for If-Modified-Since and If-None-Match headers (only if not a timeout page)
                if not timeoutpage and self.handler.handleIfModifiedSince(etag, lmod):
                    f.close()
                    return None  # don't send a file that didn't change
                else:
                    self.handler.send_response(200)
                    if timeoutpage and passthroughResponse:
                        # add a session cookie on the timeout page, to replace the old session
                        cookie=passthroughResponse.getCookies()[SESSION_COOKIE_NAME]
                        headers["Set-Cookie"]=cookie.OutputString()
                    for h,v in headers.iteritems():
                        self.handler.send_header(h,v)
                    self.handler.send_header("Content-Type",ctype)
                    self.handler.content_length = stats.st_size
                    self.handler.send_header("ETag", etag)
                    self.handler.send_header("Last-Modified", lmod)
                    self.handler.send_header("Expires",self.handler.date_time_string(time.time()+31*24*3600))
                    self.handler.send_header("Cache-Control", 'public, max-age=86400, x-gzip-ok="public, no-transform"')
                    if compress == True:
                      self.handler.send_header("Content-Encoding", "gzip")
                      # we trust browser-side caching won't force us to do this very often
                      # TODO: implement a pre-compressed file caching mechanism
                      c = self.webapp.getContext()
                      try:
                        # if the webapp defines its own mechanism for gzip caching
                        # (as does Yaki), then try to use it
                        if stats.st_mtime <= c.gzipcache.mtime(fspath):
                          zbuffer = c.gzipcache[fspath]
                          self.handler.send_header("X-Pre-Compressed","True")
                        else:
                          raise IOError
                      except:
                        zbuf = cStringIO.StringIO()
                        zfile = gzip.GzipFile(mode = 'wb',  fileobj = zbuf, compresslevel = zlib.Z_BEST_COMPRESSION)
                        zfile.write(f.read())
                        zfile.close()
                        zbuffer = zbuf.getvalue()
                        try:
                          c.gzipcache[fspath] = zbuffer
                        except:
                          pass
                      self.handler.send_header("Content-Length",len(zbuffer))
                    else:
                      self.handler.send_header("Content-Length",stats.st_size)
                    self.handler.end_headers()
                if passthroughResponse:
                    passthroughResponse.header_written=True
            if not headOnly:
                if compress == True:
                     return cStringIO.StringIO(zbuffer)
                return f
        def do_POST(self):
            self.handler.send_error(501, "Can only POST to scripts (not static pages), or your POST url is invalid.")

    def getPageProcessor(self, path, handler):
        def is_static(path, pathpart):
            fullpath=self.getFullPath(pathpart)   # only consider pathpart
            # see if we can locate the file, if not, try with .html/.htm suffixes. (not with favicon.ico)
            if os.access(fullpath, os.R_OK):
                return pathpart,''
            elif pathpart=="favicon.ico":
                return None
            elif os.access(fullpath+".html", os.R_OK):
                return pathpart+".html",''
            elif os.access(fullpath+".htm", os.R_OK):
                return pathpart+".htm",''
            else:
                return None

        def is_snakelet(path, pathpart):
            # Test whether path corresponds to a snakelet.
            # Return a tuple (snakeleturl, pathinfo) if path requires running a snakelet, None if not.
            # This method is defined in the class scope because it is used from the server directly
            # in certain cases.
            for snake in self.snakelets:        # slow: linear search, but cannot be avoided because of patterns
                if '*' in snake or '?' in snake or ('[' in snake and ']' in snake):
                    if fnmatch.fnmatchcase(pathpart, snake):
                        pathinfo=path[len(pathpart):]  # check if the pathinfo is okay
                        if not pathinfo or pathinfo[0]=='/' or pathinfo[0]=='?':
                            return (snake, '')  # no pathinfo for fnmatched snakelets
                else:
                    if path.startswith(snake):
                        pathinfo=pathpart[len(snake):]
                        if not pathinfo or pathinfo[0]=='/':
                            return (snake, pathinfo)  # don't unquote yet!
            return None

        def is_Ypage(path, pathpart):
            # Test whether path corresponds to an Ypage.
            # Return a tuple (ypageurl, pathinfo) if path requires running an Ypage, None if not.
            # Does also check if the referenced ypage actually exists, if not, return None.
            _suffix=".y"
            fullpath=self.getFullPath(pathpart)
            if pathpart.endswith(_suffix):
                if os.access(fullpath, os.R_OK):
                    return (pathpart,'') # no pathinfo because .y is last in path
                else:
                    return None # requested ypage doesn't exist
            else:
                if os.access(fullpath+_suffix, os.R_OK):   # try again after appending ".y"
                    return (pathpart,'') # no pathinfo when found this way
                pathpart=pathpart.split(_suffix+"/",1)  # check for path components...
                # XXX this does not find any ypages that may exist as part of the path (by appending .y to the components)
                if len(pathpart)>1:
                    return (pathpart[0]+_suffix,'/'+pathpart[1])
            return None

        # Check for the various page types (snakelet, Ypage) and if one is found, return appropriate processor.
        pathpart,query = urllib.splitquery(path)

        result=is_snakelet(path, pathpart)
        if result:
            return WebApp.SnakeletProcessor(self, handler, result[0], result[1], query)
        result=is_Ypage(path, pathpart)
        if result:
            return WebApp.YpageProcessor(self, handler, result[0], result[1], query)
        result=is_static(path, pathpart)
        if result:
            return WebApp.StaticProcessor(self, handler, result[0], result[1], query)
        return None

    def _have_index_snakelet(self, path, indexname="index.sn"):
        # Check if there is an index.sn snakelet for the given path.
        path+=indexname
        for snake in self.snakelets:        # slow: linear search, but cannot be avoided because of patterns
            if fnmatch.fnmatchcase(path, snake):
                if snake.endswith(indexname):     # explicit index.sn is required in the pattern
                    return True
        return False

    def serveStaticFile(self, filename, response, useResponseHeaders=False):
        # public API method to serve static files from a snakelet or things like that.
        processor=WebApp.StaticProcessor(self, response.server, None, None, None)
        headers={}
        if useResponseHeaders:
            headers = response.userHeaders
            if response.content_disposition:
                headers["Content-Disposition"]=response.content_disposition
        fh=processor.serveStaticFile(False, None, filename, headers)
        if fh:
            response.server.copyfile(fh, response.server.wfile)
            fh.close()
        response.setRedirectionDone() # bit of a hack to flag the response object as 'used'
        del response.outs  # avoid usage of the output stream afterwards


    def addPageHeaders(self, snakelet, response):
        if snakelet.allowCaching():
            # add last-modified header
            (etag, lmod) = self.create_ETag_LMod_headers(snakelet.getMTime(), 0, id(snakelet))
            response.setHeader("ETag",etag)
            response.setHeader("Last-Modified",lmod)
            response.setHeader("Pragma","whatever")
            response.setHeader("Cache-Control","public")
            response.setHeader("Expires",response.server.date_time_string(time.time()+60*15))
        else:
            # adds 'no-cache' headers to response object
            response.setHeader("Pragma","no-cache")     #  for http 1.0 clients
            response.setHeader("Cache-Control", "no-cache, max-age=0, must-revalidate")
            response.setHeader("Expires", response.server.date_time_string())

    def sendPageHeaders(self, snakelet, handler):
        # send headers directly (for snakelets and ypages, HEAD requests)
        if snakelet.allowCaching():
            # add last-modified header
            (etag, lmod) = self.create_ETag_LMod_headers(snakelet.getMTime(), 0, id(snakelet))
            handler.send_header("ETag",etag)
            handler.send_header("Last-Modified",lmod)
            handler.send_header("Pragma","whatever")
            handler.send_header("Cache-Control","public")
            handler.send_header("Expires", handler.date_time_string(time.time()+60*15))
        else:
            handler.send_header("Pragma","no-cache")     #  for http 1.0 clients
            handler.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
            handler.send_header("Expires", handler.date_time_string())

    def allowDirListing(self, path):
        # allow directory listing of this path?? (relative path)
        return self.dirListAllower(self._getPath(path))

    def allowDocument(self, path):
        # allow this document? (relative path)
        return self.documentAllower(self._getPath(path))

    def run_snakelet(self, handler, context, pathinfo, query, passthroughRequest=None, passthroughResponse=None, HEADrequestOnly=False):
        snake = self.snakelets[context]
        module=inspect.getmodule(snake.__class__)    # python 2.3 bug can't handle objects, need class here
        srcfile=inspect.getsourcefile(module)
        stats=os.stat(srcfile)
        if stats.st_mtime > snake.getMTime():
            # source file is newer, reload the snakelet module
            log.debug("reloading snakelet module '%s'" % module.__name__)
            reload(module)
            # replace any snakelet objects that are defined in this module
            for pattern, snk in list(self.snakelets.items()):
                if inspect.getmodule(snk.__class__) is module:   # same python 2.3 bug workaround as above
                    clz=getattr(module, snk.__class__.__name__)
                    self.snakelets[pattern]=clz(pattern, weakref.ref(self)) # create new snakelet instance.
            snake = self.snakelets[context]

        if HEADrequestOnly:
            handler.send_response(200,"OK")
            self.sendPageHeaders(self.snakelets[context], handler)
            return

        req=None
        resp=None

        try:
            if passthroughRequest:
                # we were called as a result of redirecting or including in another request
                req=passthroughRequest
                # By design, the new query args are NOT PARSED,
                # so DO NOT DO THIS: req._init_query(pathinfo,query)
            else:
                req = request_response.Request(self, pathinfo, query, handler, handler.rfile)

            resp=passthroughResponse or request_response.Response(self, handler, handler.wfile)

            # add the session. Note that for ypages, this is done in the YpageEngine instead.
            if snake.requiresSession() != snakelet.Snakelet.SESSION_NOT_NEEDED:
                try:
                    session = self.addSessionCookie(req,resp, snake.requiresSession()!=snakelet.Snakelet.SESSION_DONTCREATE)
                    if session and session.timeout and self.sessionTimeoutPage and not resp.beingRedirected():
                        timeoutpage = urllib.basejoin(self.urlprefix,self.sessionTimeoutPage)
                        snake.redirect(timeoutpage, req, resp)
                        return
                except TooManySessions:
                    resp.sendError(503,"too many sessions")
                    return

            # check the session requirements
            if snake.requiresSession()==snakelet.Snakelet.SESSION_REQUIRED and session.isNew():
                resp.sendError(403, "Your session must be synchronised (not new) to access this page. Are cookies switched off?")
                return
            elif snake.requiresSession()==snakelet.Snakelet.SESSION_LOGIN_REQUIRED and not session.getLoggedInUser():
                authmethod = snake.getAuthMethod() or self.authMethod
                httpuser=None
                if authmethod:
                    try:
                        (httpuser, httppasswd, httpprivileges) = self.handleAuthMethod(req, resp, snake)
                        self.loginAuthenticatedUser(httpuser, httppasswd, httpprivileges, snake, req, resp)
                    except AbortPage:
                        return
                else:
                    resp.sendError(403, "You must be logged in to access this page")
                    return

            if snake.getAuthorizedRoles():
                if not session.getLoggedInUser().hasAnyPrivilege(snake.getAuthorizedRoles()):
                    self.handleNotPrivileged(req,resp,snake)
                    return

            if not self.checkAuthorizationPatterns(req, resp, snake):
                # user priv check failed against auth patterns. HTTP response has already been given.
                return

            self.addPageHeaders(snake,resp)

            resp.setEncoding(self.defaultOutputEncoding)
            resp.setContentType(self.defaultContentType or "text/html")

            snake.serve(req, resp)          # <------ the actual call to the snakelet!

            if not resp.used():
                resp.sendError(404,"snakelet had no output")

        except Exception,x:
            self.reportSnakeletException(snake, x, handler, handler.wfile, req, resp, snake.getErrorPage())
            # done... error has also been sent to the client.
            return


    def checkAuthorizationPatterns(self, req, resp, snake, handler=None):
        if self.authorizationPatterns:
            if not resp:
                resp=request_response.Response(self, handler, handler.wfile)
            if not req:
                req=request_response.Request(self, "", "", handler, handler.rfile)
                # Try to add a session, if a cookie exists. Otherwise, do nothing.
                # We do this, to be able to deal with things like pictures
                # that get loaded from within a web app (but are static content,
                # so they're not handled by the webapp but by the server directly...)
                try:
                    session = self.addSessionCookie(req,resp, False)
                except TooManySessions:
                    resp.sendError(503,"too many sessions")
                    return
            session=req.getSession()
            requiredRoles=[]
            url=req.getRequestURLplain()
            for (pat,privs) in self.authorizationPatterns.items():
                if fnmatch.fnmatchcase(url, pat) or \
                   fnmatch.fnmatchcase(url+".y", pat) or \
                   fnmatch.fnmatchcase(url+".html", pat) or \
                   fnmatch.fnmatchcase(url+".htm", pat):
                    if privs is None:
                        return True     # None means: "except this one"; no privileges required for this url
                    requiredRoles.append(privs)

            if self.authorizationPatterns and requiredRoles:
                if snake and snake.requiresSession()==snakelet.Snakelet.SESSION_NOT_NEEDED:
                    raise httpauth.AuthError("page must have sessiontype other than 'no' because of authorization patterns")
                if not session or not session.getLoggedInUser():
                    try:
                        (httpuser, httppasswd, httpprivilegesOrUser) = self.handleAuthMethod(req,resp,snake)
                        # check if the authenticated user has required roles.
                        privs = httpprivilegesOrUser
                        if isinstance(httpprivilegesOrUser, LoginUser):
                            privs = httpprivilegesOrUser.privileges
                        for roles in requiredRoles:
                            if not roles.intersection(privs):
                                self.handleNotPrivileged(req,resp,snake)
                                return False
                        self.loginAuthenticatedUser(httpuser, httppasswd, httpprivilegesOrUser, snake, req, resp)
                        return True
                    except AbortPage:
                        pass
                    return False
                user=session.getLoggedInUser()
                for roles in requiredRoles:
                    if not user.hasAnyPrivilege(roles):
                        self.handleNotPrivileged(req,resp,snake)
                        return False
        # if we get here, the request is allowed.
        return True


    def loginAuthenticatedUser(self, httpuser, httppasswd, privilegesOrUser, snake, request, response):
        # notice that 'privilegesOrUser' may be a set/list of privileges, or a snakelet.user.LoginUser object instance
        if snake and privilegesOrUser is not None and snake.requiresSession()!=snakelet.Snakelet.SESSION_NOT_NEEDED:
            if isinstance(privilegesOrUser, LoginUser):
                userobject = privilegesOrUser
            else:
                userobject = LoginUser(httpuser,httppasswd, privileges=privilegesOrUser, escrow=self.escrow)

            if isinstance(snake, Ypage):
                if not hasattr(snake,"User") or not snake.User:
                    log.debug("logging in user: %s,%s",httpuser,privilegesOrUser)
                    request.getSession().loginUser(userobject)
                    self.pageEngine.addPageVars(snake, self, request, response)  # make sure page.User has been set
            else:
                if not request.getSession().getLoggedInUser():
                    log.debug("logging in user: %s,%s",httpuser,privilegesOrUser)
                    request.getSession().loginUser(userobject)


    def handleAuthMethod(self,req,resp,snake):
        # note that Single-signon cannot be done here. You need to enable sharedSession for that.
        authmethod=autharg=None
        if snake:
            authmethod=snake.getAuthMethod()
        if authmethod:
            authmethod, autharg = authmethod
        elif self.authMethod:
            authmethod, autharg = self.authMethod
        if not authmethod:
            resp.sendError(403, "You must be logged in to access this page")
            raise AbortPage
        if authmethod in ("httpbasic", "httpdigest"):
            if not self.authorizeUser:
                raise httpauth.AuthError("no http user authenticator defined in webapp")
            try:
                (httpuser,httppassword,httpprivileges) = httpauth.HTTPauthenticate(req, resp, req.getRequestURLplain(), self.authorizeUser, authMethod=authmethod, authRealm=autharg or snake.getURL())
                log.debug("http auth results: %s,%s",httpuser,httpprivileges)
                return httpuser, httppassword, httpprivileges
            except httpauth.AuthError, x:
                if req.getSession():
                    req.getSession().logoutUser()
                log.error( "AUTH ERROR "+str(x) )
                raise AbortPage
        elif authmethod=="loginpage":
            signinPage=autharg
            if signinPage:
                # set the after-login-page on the request context, will be processed by loginpage logic later
                req.getContext()._SNKLOGIN_RETURNPAGE=req.getBaseURL()+req.getRequestURL()
                signinPage=urllib.basejoin(self.urlprefix,signinPage)
                if signinPage==req.getRequestURL():
                    log.warn("signinPage is not accessible (authorization required to view it!?): "+signinPage)
                    resp.sendError(403, "The signin page is not accessible due to a server misconfiguration")
                else:
                    req.server.redirect(signinPage, req, resp)
                    log.debug("redirected to signin page: %s",signinPage)
            else:
                resp.sendError(403, "You must be logged in to access this page")
            raise AbortPage # make sure that the current page is not displayed, but the login page (or the error page)
        else:
            raise httpauth.AuthError("invalid authentication method: "+authmethod)


    def handleNotPrivileged(self, req, resp, snake):
        resp.sendError(403, "You don't have the required privileges to access this page")

    def reportSnakeletException(self, snakelet, exc, handler, out, request, response, errorpage=None):
        # oops something went wrong, print the traceback.
        errorpage = errorpage or self.defaultErrorPage
        typ, value, tb = sys.exc_info()
        sys.exc_clear()

        if type(typ)==types.StringType:
            name=typ
        else:
            name=typ.__name__

        snk_url = "?"
        if snakelet:
            snk_url = snakelet.getURL()
        log.error("PAGE '"+snk_url+"' threw exception: "+name+": "+str(value))
        log.error("TRACEBACK: "+"".join(traceback.format_tb(tb)))  # log the traceback as well

        if handler:
            response.setResponse(500,"Internal server error")
        if errorpage and request:
            # custom error page
            try:
                ctx=request.getContext()
                # place the exception information on the request context
                ctx.Exception=exc
                ctx.Exception_page=snakelet.getURL()
                ctx.Exception_type=typ
                ctx.Exception_value=value
                ctx.Exception_tb=tb
                snakelet.redirect(errorpage,request,response)  # this will erase any output that was already done
                del ctx.Exception      # avoid cyclic refs
                del ctx.Exception_tb   # avoid cyclic refs
                return
            except Exception,x:
                del tb
                # OUCH, couldn't redirect to error page
                return self.reportSnakeletException(snakelet,x,handler,out,request,response,None)
        else:
            if not response.used():
                response.writeHeader()
            out.write("<html><head><title>Server error</title></head><body><hr /><h2>Exception in server</h2>\n")
            out.write("<h3>Page &quot;"+snk_url+"&quot; caused an error: "+cgi.escape(str(value))+"</h3>\n")
            if hasattr(exc, 'Snakelets_extrainfo'):
                out.write("<h3>Extra information:</h3>"+exc.Snakelets_extrainfo)
            out.write("<H3>Traceback (innermost last):</H3>\n")
            lst = traceback.format_tb(tb) + traceback.format_exception_only(typ, value)
            out.write("<PRE>%s<strong>%s</strong></PRE></body></html>\n" % ( cgi.escape("".join(lst[:-1]),1), cgi.escape(lst[-1],1) ) )
        return None

    # run the given Ypage. The ypage must exist.
    def run_Ypage(self, handler, path, pathinfo, query, passthroughRequest=None, passthroughResponse=None, HEADrequestOnly=False):
        fullpath=self.getFullPath(path)
        if not fullpath.endswith(".y"):
            fullpath+=".y"   # add missing suffix to 'smart loaded' paths

        errorpage=None
        page=None
        req=None
        resp = passthroughResponse or request_response.Response(self,handler,handler.wfile)

        try:
            if passthroughRequest:
                # we were called as a result of redirecting or including in another request
                req=passthroughRequest
                # By design, the new query args are NOT PARSED,
                # so DO NOT DO THIS: req._init_query("",query)
            else:
                req=request_response.Request(self, pathinfo, query, handler, handler.rfile)

            outputEncoding = contentType = contentDisposition = None

            try:
                page = self.pageEngine.loadPage(fullpath,path,self)     # new Page instance
                if HEADrequestOnly:
                    # only send the required headers for the HEAD request
                    handler.send_response(200,"OK")
                    self.sendPageHeaders(page, handler)
                    return None

                # Add session, and some shortcut attributes to the ypage:
                try:
                    self.pageEngine.addPageVars(page, self, req, resp)
                    session=req.getSession()
                    if session and session.timeout and self.sessionTimeoutPage and not resp.beingRedirected():
                        timeoutpage = urllib.basejoin(self.urlprefix,self.sessionTimeoutPage)
                        page.redirect(timeoutpage, req, resp)
                        return None
                except TooManySessions:
                    return resp.sendError(503,"too many sessions for your IP address")

                # check the session requirements
                if page.requiresSession()==snakelet.Snakelet.SESSION_REQUIRED:
                    session=req.getSession()
                    if not session or session.isNew():
                        return resp.sendError(403, "Your session must be synchronised (not new) to access this page. Are cookies switched off?")
                elif page.requiresSession()==snakelet.Snakelet.SESSION_LOGIN_REQUIRED and (not hasattr(page,"User") or not page.User):
                    authmethod = page.getAuthMethod() or self.authMethod
                    httpuser=None
                    if authmethod:
                        try:
                            (httpuser,httppassword,httpprivileges) = self.handleAuthMethod(req, resp, page)
                            self.loginAuthenticatedUser(httpuser, httppassword, httpprivileges, page, req, resp)
                        except AbortPage:
                            return None
                    else:
                        resp.sendError(403, "You must be logged in to access this page")
                        return None

                if page.getAuthorizedRoles():
                    if not page.User.hasAnyPrivilege(page.getAuthorizedRoles()):
                        self.handleNotPrivileged(req,resp,page)
                        return None

                if not self.checkAuthorizationPatterns(req, resp, page):
                    # user priv check failed against auth patterns. HTTP response has already been given.
                    return None

                errorpage = page.getErrorPage()
                
                # --- the actual page call follows
                output, outputEncoding, (contentType, contentDisposition) = self.pageEngine.runPage(page,req,resp, self.defaultOutputEncoding)

            except CompilerError,cx:
                if HEADrequestOnly:
                    return resp.sendError(500)
                output=cStringIO.StringIO()
                log.error("Ypage-compiler error: "+str(cx))
                # oops something went wrong, print the traceback.
                output.write("<html><head><title>Server error</title></head><body><hr /><h2>Exception in server</h2>\n")
                output.write("<h3>Error compiling page &quot;"+path+"&quot;: "+str(cx)+"</h3>")
                if hasattr(cx, 'Snakelets_extrainfo'):
                    output.write("<h3>Extra information:</h3>"+cx.Snakelets_extrainfo)
                output.write("<h4>More info can be found in the server output or log.</h4></body></html>\n")
                outputEncoding=contentType=contentDisposition=None

            if outputEncoding:
                resp.setEncoding(outputEncoding)
            if contentType:
                resp.setContentType(contentType)
            if contentDisposition:
                resp.setContentDisposition(contentDisposition)

            length=output.tell()
            output.seek(0)
            resp.setContentLength(length,True)      # force the correct content-length
                
            if not resp.used():
                resp.writeHeader()

            return output

        except EnvironmentError,x:
            log.debug( "404-->generic io error "+str(x)+" path="+path)
            handler.send_error(404)
            return None
        except Exception,x:
            self.reportSnakeletException(page,x, handler, handler.wfile, req, resp, errorpage)
            # done, error has been reported
            return None

    def clearCache(self):
        self.pageEngine.clearCache()


    def addSessionCookie(self,request, response, create=True):
        self.lock.acquire()

        try:
            if request.session:
                # already got the session, don't try again
                return request.session

            # try to find the current session ID and associated Session object
            timeout=False
            sessionIDs=request.getCookies().get(SESSION_COOKIE_NAME, [])
            sessionIDs.extend(request.getCookies().get(SESSION_COOKIE_NAME_SHARED, []))

            if sessionIDs:
                # log.debug("---Searching Session "+str(sessionIDs))
                # we may have multiple session ids... try them all
                for sessionID in sessionIDs:
                    session=self.sessions.get(sessionID)
                    # note: shared sessions are already present in all webapps that have sharedSession,
                    # so no explicit search across webapps is needed.
                    if session:
                        request.setSession(session)
                        session.touch()   # update last-used timestamp
                        session.setRequestData(request,response)
                        return session
                else:
                    # no session found with the session id that the request gave us,
                    # so we assume that there has been a session timeout.
                    timeout=True
                    # Notice that a new session will be created a few lines down.
                    # This is okay, because the requested page needs a session...
                    # and if the user continues on the site, this new session is used.
                    # So no additional session is created (no waste of memory)

            if not create:
                return None

            # No session cookie or invalid, set a new one, create new session,
            # but check if we still allow new sessions for this remote address
            remoteAddr = str(request.getRealRemoteAddr())
            if len([None for sess in self.sessions.values() if sess.remoteAddr==remoteAddr]) >= MAX_SESSIONS_PER_IP:
                log.warn("Too many sessions for remote address "+str(remoteAddr)+"; refused")
                del request, response
                raise TooManySessions

            # create a new unique session id
            while True:
                sessionID=hashlib.sha1(remoteAddr+time.ctime()+str(time.time())+str(random.random())).hexdigest()
                if sessionID not in self.sessions:
                    break
            session=websession.Session(sessionID, self.sessionTimeoutSecs, remoteAddr, weakref.ref(self))
            session.timeout=timeout
            session.shared=self.sharedSession
            if self.sharedSession:
                tld = {}
                if self.sharedSessionTLD:
                    tld['domain'] = self.sharedSessionTLD
                response.setCookie(SESSION_COOKIE_NAME_SHARED,sessionID,path=self.server.serverURLprefix+"/", **tld)
            else:
                response.setCookie(SESSION_COOKIE_NAME,sessionID,path=self.urlprefix)
            self.server.registerSession(self, session)
            request.setSession(session)
            session.setRequestData(request,response)
            return session
        finally:
            self.lock.release()

    def _deleteSession(self, session, response=None, checkShared=True):
        # Remove a session from the session registry, and if response is not None,
        # also let it remove the session cookie.
        self.lock.acquire()
        try:
            del self.sessions[session.getID()]
            if self.sharedSession and checkShared:
                self.server.removeSharedSession(session, self.getVirtualHost()[0], self.name[0])
            if response:
                if self.sharedSession and checkShared:
                    response.delCookie(SESSION_COOKIE_NAME_SHARED, path=self.server.serverURLprefix+"/")
                else:
                    response.delCookie(SESSION_COOKIE_NAME, path=self.urlprefix)
        finally:
            self.lock.release()

    def precompileYPages(self):
        log.info("Precompiling all Ypages...")
        errorlist=[]
        # recursively scans the document root and subdirs to precompile all .y pages.
        striplen=len(os.path.join(self.docrootFSPath, "abc"))-3
        for (dirname, dirs, files) in os.walk(self.docrootFSPath):
            if 'CVS' in dirs:
                dirs.remove('CVS')  # do not walk CVS directories
            if '.svn' in dirs:
                dirs.remove('.svn') # do not walk Subversion directories
            for filen in files:
                if filen.endswith(".y"):
                    # aha, found a .y page. Load (=compile) it.
                    entrypath=os.path.join(dirname[striplen:], filen)
                    fullpath=self.getFullPath(entrypath)
                    try:
                        self.pageEngine.loadPage(fullpath,entrypath,self)   # discard the result :-)
                    except CompilerError,x:
                        log.error("ERROR COMPILING YPAGE "+filen)
                        errorlist.append( (entrypath, str(x) ) )

        if errorlist:
            msg="THERE WERE %d ERRORS IN THE YPAGES OF WEBAPP '%s'" % (len(errorlist), self.name[0] )
            print >>sys.stderr,msg, "(see log, at the end)"
            log.error(msg)
            log.error("Errors follow:")
            for (url,error) in errorlist:
                log.error( "%s  :  %s" % (url,error) )
            raise WebAppInitialisationError


    def create_ETag_LMod_headers(self, timestamp, size, locationid):
        now=time.time()
        if timestamp>now:
            timestamp=now   # no dates in the future
        etag='%x%x%x' % (timestamp,size,locationid)
        etag='"%s"' % binascii.b2a_base64(etag).strip()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
        datestr = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
            self.weekdayname[wd],
            day, self.monthname[month], year,
            hh, mm, ss)
        return (etag, datestr)

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None,'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
