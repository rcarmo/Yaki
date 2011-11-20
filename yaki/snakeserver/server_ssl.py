#############################################################################
#
#	$Id: server.py,v 1.162 2005/03/19 22:56:53 irmen Exp $
#	The HTTP Server
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import os, time, sys, types, copy, cStringIO, threading
import urllib, urllib2, socket, select, shutil
import BaseHTTPServer, mimetypes
import logging, logging.config
import util
import webapp
import plugin

SNAKELETS_VERSION = "Snakelets 1.38"

THREADING_ENABLED=True     # False for better debugging, True for multithreaded server.
IS_SSL=True
try:
    from tlslite.api import *
except ImportError:
    IS_SSL=False

if IS_SSL:
    s = open("./localhost.crt").read()
    x509 = X509()
    x509.parse(s)
    certChain = X509CertChain([x509])
    
    s = open("./localhost.private.key").read()
    privateKey = parsePEMKey(s, private=True)
    
    sessionCache = SessionCache()
  


log=None            # will be set by main()
accesslog=None      # will be set by main()


try:
    # try to import the sendfile wrapper module from http://www.snakefarm.org/
    from sendfile import sendfile
except ImportError:
    # no sendfile available
    sendfile=None


class InvalidConfigurationException(Exception): pass


#
#   The actual HTTP request handler used by the HTTP server.
#   Doesn't use SimpleHTTPServer because that one is TOO simple
#   and has many features we override anyhow.
#
class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    rbufsize = -1       # input stream is fully buffered
    wbufsize = 1024     # a little buffering on the output stream

    snakelets_version = SNAKELETS_VERSION
    server_version = SNAKELETS_VERSION.replace(' ','/')
    protocol_version = "HTTP/1.1"
 
    error_message_format = """\
<head>
<title>Error %(code)d</title>
</head>
<body>
<h1>Error response</h1>
<p>%(code)s = %(explain)s.
<p>Server message: %(message)s.
<p><hr><address>"""+server_version+" Python/"+sys.version.split()[0]+"<br>If the problem remains, please contact webmaster @ this domain.</body>"

    # extensions_map contains the mime type definitions.
    extensions_map=mimetypes.types_map.copy()
    extensions_map.update(
      {
        "": "text/plain", # Default, *must* be present
        ".mp3"  : "audio/mpeg",
        ".m3u"  : "audio/x-mpegurl",
        ".y"    : "text/html",
        ".py"   : "text/plain",
        ".jar"  : "application/x-jar",
        ".class": "application/x-java-class",
        ".ogg"  : "application/ogg",
        ".gz"   : "application/x-gzip",
        ".bzip" : "application/x-bzip2",     # not sure
        ".bz2"  : "application/x-bzip2",     # not sure
        ".tgz"  : "application/x-gzip-tar"   # not sure
      }
    )

    def setup(self):
        import struct
        linger=struct.pack("ii", 1, 20 )
        self.request.setsockopt ( socket.SOL_SOCKET, socket.SO_LINGER, linger) # XXX not sure if this helps agains prematurely destroyed sockets...
        if self.server.debugRequests:
            log.debug(">>>>> GOT HTTP REQUEST #%d, from %s" % (self.server.requestCounter, self.client_address[0] ) )
        BaseHTTPServer.BaseHTTPRequestHandler.setup(self)
        self.startTimeCPU=time.clock()
        self.startTimeReal=time.time()
        
    def finish(self):
        try:
            BaseHTTPServer.BaseHTTPRequestHandler.finish(self)
        except socket.error,x:
            log.info("Socket error during flush: "+str(x))
        if self.raw_requestline:    # only postprocessing of real requests
            try:
                self.processTimeCPU = time.clock() - self.startTimeCPU
                self.processTimeReal = time.time() - self.startTimeReal
                # ... do something with process time?
                if self.server.debugRequests:
                    log.debug( "<<<<< REQUEST TOOK: %d msec. CPU, %d msec. real" % ( int( self.processTimeCPU * 1000), int( self.processTimeReal * 1000) ) )
                self.logRequestInfo()
            except Exception,x:
                log.error("Error during finish: %s",x)
        if self.server.debugReloading:
            self.server.reloadAllModules()

    def handle_one_request(self):
        """Handle a single HTTP request. overridden from base class"""
        self.response_code=''
        self.content_length=''
        self.raw_requestline = self.rfile.readline()
        if self.server.debugRequests:
            log.debug( "REQUEST="+self.raw_requestline.rstrip() )
        if not self.raw_requestline:
            self.close_connection = 1
            log.debug("Ignored empty request")
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return
        if self.server.debugRequests:
            log.debug( "HEADERS FOLLOW:")
            log.debug( self.headers )
            log.debug( "--- end of headers")

        (self.virtualhost, self.virtualhostport)=urllib.splitport( self.headers.get("host", "") )
        # if we're running behind a proxy (apache), get the hostname from another header:
        x_host = self.headers.get("X-Forwarded-Host")
        if x_host:
            (self.virtualhost , self.virtualhostport)=urllib.splitport(x_host)

        if not self.virtualhost:
            # no Host header, pick default host
            self.virtualhost, self.virtualhostport = self.server.defaultVirtualHost
        
        self.virtualhostport=self.server.externalPort or int(self.virtualhostport)   #  XXX hard override of the port...
        
        if self.server.debugRequests:
            log.debug("REQUEST IS FOR VHOST %s : %d" % (self.virtualhost, self.virtualhostport))
                
        self.server.requestCounter+=1
        mname = 'do_' + self.command
        if not hasattr(self, mname):
            self.send_error(501, "Unsupported method (%s)" % `self.command`)
            return
        method = getattr(self, mname)
        method()

    def do_PING(self):
        self.path='/'
        self.send_error(202)  # 'accepted'
                
    def do_GET(self):
        self.path=self.checkRelativePath(self.path)
        if self.path:
            f=self.do_GETorHEAD()
            if f:
                self.copyfile(f,self.wfile)
                f.close()

    def do_HEAD(self):
        self.path=self.checkRelativePath(self.path)
        if self.path:
            f=self.do_GETorHEAD()
            if f:
                f.close()

    def do_POST(self):
        self.path=self.checkRelativePath(self.path)
        if self.path:
            # Handle form POST requests.
            web=self.server.getWebApp(self.path, self.virtualhost)
            f=web.do_POST(self)
            if f:
                self.copyfile(f,self.wfile)
                f.close()
        
    def checkRelativePath(self, path):
        # Check path for relative things like foo/./bar and /foo/../bar/ (will be refused)
        if path.find('/./')>=0 or path.find('/../')>=0:
            self.send_error(400, "Unsupported url path notation with relative directories")
            return None
        return path

    def kill(self):
        try:
            # kill the socket connection. XXX only works on unix?
            self.connection.close()
            # use low-level IO to close streams, otherwise we block...
            os.close(self.wfile.fileno())
            os.close(self.rfile.fileno())
        except:
            pass

    # Some logging methods overridden from BaseHTTPRequestHandler
    # They do nothing!! We do our own logging (better :-)
    def log_request(self, *args):   pass
    def log_error(self, *args):     pass
    def log_message(self, *args):   pass


    def logRequestInfo(self):
        # write a request to the access log.
        if accesslog.isEnabledFor(logging.INFO):
            format='%s - - [%s] "%s" %s %s "%s" "%s"' 
            useragent=self.headers.getheader('user-agent') or '-'
            referer=self.headers.getheader('referer') or '-'
            size=str(self.content_length) or '-'
            args=( self.address_string(), self.log_date_time_string(), self.raw_requestline.strip(), str(self.response_code) or '?', size, referer, useragent )
            accesslog.info( format%args )
                          
    def do_GETorHEAD(self, passthroughRequest=None, passthroughResponse=None):
        # common code for GET and HEAD requests. (supports scripts / snakelets)
        web=self.server.getWebApp(self.path, self.virtualhost)
        if not web:
            self.send_error(404,"File not found (no context enabled for URL "+self.path+")")
            return

        realpath, query = urllib.splitquery(self.path)
        fspath = urllib.url2pathname(realpath)
        fspath = os.path.normpath(os.path.join(web.getDocRootPath(), fspath[len(web.getURLprefix()):]))
        # check if the actual filesystem object still lies in the webapp
        # (due to url hacking --inserting slashes, dots, etc-- this may no longer be the case)
        if not fspath.startswith(web.getDocRootPath()):
            self.send_error(403)    # denied
            return
        
        # check for index pages if path is a directory
        if os.path.isdir(fspath):
            if realpath.endswith('/'):
                ## Allow webapps to set their own array of index pages.
                ## Former value of following line: for index in self.server.INDEXPAGES:
                for index in web.indexPages:
                    indexf = os.path.join(fspath, index)
                    if os.path.exists(indexf):
                        fspath = indexf
                        self.path=os.path.join(realpath,index)
                        if query:
                            self.path+="?"+query
                        break
                else:
                    self.path=realpath # 'forget' query args
                    return self.list_directory(web,fspath,passthroughResponse)
            else:
                if not query:   # only redirect if there are no query args
                    # path is a directory but doesn't end with '/', so send a redirect to the proper URL.
                    return self._redirectToProperDirectoryURL(urllib.unquote(self.path), passthroughResponse)

        # check if the document is allowed to be served
        if not web.allowDocument(self.path):
            if not passthroughResponse or not passthroughResponse.used():
                log.debug("404 because webapp doesn't allow loading "+self.path )
                self.send_error(404)    # not 403 forbidden..! that would let the 'hacker' know that this file *does* exist
            else:
                passthroughResponse.getOutput().write("No permission (by server config) to view document "+fspath)
            return None

        try:
            if self.command=="GET":
                return web.do_GET(self, passthroughRequest, passthroughResponse)
            elif self.command=="HEAD":
                return web.do_HEAD(self)
            else:
                if not passthroughResponse or not passthroughResponse.used():
                    self.send_error(501)
                else:
                    passthroughResponse.getOutput().write("Unsupported method "+self.command)
        except webapp.NotHandled:
            # webapp doesn't handle the url, see if there is a static file that matches.
            # this has already been done: fspath=urllib.splitquery(fspath)[0] # chop off any ?query=foo
            if not passthroughResponse or not passthroughResponse.used():
                log.debug("404 because file does not exist: "+fspath)
                self.send_error(404)
            else:
                # we're part of another request (included) so we can no longer return a HTTP status error...
                passthroughResponse.getOutput().write("Error on Page; Referenced URL not handled: "+fspath)


    def handleIfModifiedSince(self, etag, lmod):
        # Checks and handles the if-modified-since etc headers
        # If the check is positive (i.e. the resource is NOT modified),
        # returns a 304 status and True ("handled").
        # Otherwise, does nothing, and returns False ("not handled").
        IfModifiedSince=self.headers.get("If-Modified-Since",'')
        IfNoneMatch=self.headers.get("If-None-Match",'')
        if (not IfModifiedSince and not IfNoneMatch) or self.headers.get("Pragma")=='No-cache':
            return False
        index=IfModifiedSince.find(';') # strip off IE-shit
        if index>=0:
            IfModifiedSince=IfModifiedSince[:index]
        if IfNoneMatch and IfNoneMatch!='*' and etag!=IfNoneMatch:
            return False
        if lmod!=IfModifiedSince:
            return False
        self.send_response(304) # resource wasn't modified, so return 304 not modified.
        self.send_header("ETag", etag)
        self.end_headers()
        return True             # we handled this request.

# Enable this for header debugging:
#   def send_header(self, header, value):
#       log.debug(">>> HEADER: %s=%s" %(header,value) )
#       BaseHTTPServer.BaseHTTPRequestHandler.send_header(self, header, value)

    def send_error(self, code, message=None, userHeaders=None):
        # Override this from BaseHTTPRequestHandler because we need to
        # be able to send user headers across even in case of an error...
        try:
            short, lng = self.responses[code]
        except KeyError:
            short, lng = '???', '???'
        if message is None:
            message = short
        explain = lng
        self.send_response(code, message)
        self.send_header("Content-Type", "text/html")
        
        if userHeaders:
            for h,v in userHeaders.iteritems():
                self.send_header(h,v) # this was missing in the base version...
        self.end_headers()
        if self.command != 'HEAD' and code >= 200 and code not in (204, 304):
            if not self.server.plugins.serverErrorpage(self.path, code, message, explain, self.wfile):
                content = (self.error_message_format %  {'code': code, 'message': message, 'explain': explain})
                self.wfile.write(content)
            self.wfile.flush()
    
    def send_response(self, code, msg=None):
        # Override this from BaseHTTPRequestHandler because we need to
        # send some headers at every response no matter what...
        BaseHTTPServer.BaseHTTPRequestHandler.send_response(self,code,msg)
        self.send_header("Connection","close")      # XXX always close the socket connection.... (HTTP pipelining is not supported)
        self.response_code=code
    
    def getServerIP(self):
        # return the IP address of the interface the request arrived on
        return self.request.getsockname()[0]

    def getServerName(self):
        if not self.virtualhostport or self.virtualhostport == 80:
            return self.virtualhost
        else:
            return '%s:%d' % (self.virtualhost, self.virtualhostport)

    def getRealServerName(self):
        return self.server.getHostName(self.getServerIP())

    def guess_type(self, path):
        # overloaded & called from base class: guess the content type
        base, ext = os.path.splitext(path)
        if self.extensions_map.has_key(ext):
            return self.extensions_map[ext]
        ext = ext.lower()
        if self.extensions_map.has_key(ext):
            return self.extensions_map[ext]
        else:
            return self.extensions_map[""]

    def getBaseURL(self):
        # XXX NO HTTPS SUPPORT.
        return 'http://'+self.getServerName()

    def list_directory(self, webapp, physicalpath, passthroughResponse=None):
        # overloaded & called from base class: list directory contents. Don't list forbidden dirs
        # Note that self.path has already been adjusted for the webapp.
        path=urllib.unquote(self.path)
        if not webapp.allowDirListing(path):
            if not passthroughResponse or not passthroughResponse.used():
                self.send_error(403)
            else:
                passthroughResponse.getOutput().write("No permission (by server config) to list directory "+path)
            return None
        if path and not path.endswith('/'):
            # it doesn't end in a slash, send a redirect WITH a slash
            return self._redirectToProperDirectoryURL(path,passthroughResponse)
        # path ends in '/' and is allowed to be listed.
        try:
            dirlister = self.server.getPlugin("DirLister")
            f = cStringIO.StringIO()
            dirlister.listDir(physicalpath, path, f)
            size=f.tell()
            f.seek(0)
            if not passthroughResponse or not passthroughResponse.used():
                self.send_response(200,"Directory content follows")
                self.send_header("Content-type", "text/html")
                self.send_header("Content-length", str(size))
                self.content_length=size
                self.end_headers()
            if self.command=="HEAD":
                return None
            return f
        except os.error:
            if not passthroughResponse or not passthroughResponse.used():
                self.send_error(403)
            else:
                passthroughResponse.getOutput().write("No permission to list directory "+path)
            return None
            
    def _redirectToProperDirectoryURL(self, path, passthroughResponse):
        f=cStringIO.StringIO()
        f.write("<html><head><title>Redirection</title></head>\n"
                "<body>For correct directory listing, you're being <a href=\""+path+"/\">redirected</a>.</body></html>")
        if not passthroughResponse or not passthroughResponse.used():
            self.send_response(302, "Document moved")
            self.send_header("Content-type","text/html")
            path=self.getBaseURL()+path+'/'
            self.send_header("Location",path)
            self.end_headers()
        f.seek(0)
        return f

    def translate_path(self, path):
        # translate path to local filesystem syntax
        path = os.path.normpath(urllib.unquote(path))
        web=self.server.getWebApp(self.path, self.virtualhost)
        path = os.path.join(web.getDocRootPath(), path[len(web.getURLprefix()):])
        return path

    def copyfile(self, source, outputfile, closeSource=True):
        if sendfile and isinstance(source, file):
            # use sendfile(2) for high performance static file serving
            sfileno=source.fileno()
            size=os.fstat(sfileno).st_size
            outputfile.flush()
            sendfile(outputfile.fileno(), sfileno, 0, size)
            source.close()
        else:
            # source is not a true file or sendfile(2) is unavailable, use regular write method
            try:
                shutil.copyfileobj(source, outputfile, length=32*1024)
            except socket.error,x:
                log.error("Socket error during copyfile: "+str(x))
        try:
            outputfile.flush()
        except socket.error,x:
            log.error("Socket error during copyfile flush: "+str(x))
            # ... just ignore this error.
        if closeSource:
            source.close()

    def address_string(self):
        # override the base version that looks up the FQ hostname.
        # we just stick with the IP address...
        # ...and even take the real IP adress if we are proxied by Apache.
        host, port = self.client_address
        realhost=self.headers.get("x-forwarded-for") or host
        return str(realhost)

    def include(self, url, request, response):
        # read the other URL and write the result to the output stream.
        # Perform this in a clone of our current request handler object.
        response.initiateRedirection(url, isInclude=True)
        handler=copy.copy(self)
        #output=cStringIO.StringIO()
        #dummy=response.getDummy(output)    # work on a dummy response
        handler.doRedirect(url, request, response, True)
        #response.getOutput().write(output.getvalue())

    def redirect(self, url, request, response):
        # read the other URL and write the result to the output stream.
        # url must be absolute http://foo/bar.html  or /foo/bar.html
        response.initiateRedirection(url)
        self.doRedirect(url, request, response, False)
        response.setRedirectionDone()
        
    def doRedirect(self, url, request, response, isInclude=False):
        if not url[0]=='/':
            # assume http(s):// external url
            urlutf8=url
            if type(url)==unicode:
                urlutf8=url.encode("UTF-8")
            try:
                result=urllib2.urlopen(urlutf8)
                if result:
                    if not isInclude and not response.used():
                        # copy HTTP headers (only with redirect)
                        # overwrite, rather than add, 
                        for (header, value) in result.headers.items():
                            response.setHeader(header, value)
                        response.writeHeader()
                    response.forceFlush(self.wfile)
                    self.copyfile(result, self.wfile, False)
            except Exception,x:
                if isInclude:
                    import traceback
                    err= "".join(traceback.format_exception(*sys.exc_info()))
                    log.error("problem with including '%s': %s" % (url,err))
                    response.getOutput().write(u"<h1>Problem with including '%s':</h1><h3>%s</h3>" % (url,x))
                else:
                    response.sendError(404,"not found: "+str(x))
        else:
            # call our custom version of send_head for the new url and reusing the request object
            if urllib.splittag(url)[1] is not None:
                raise ValueError("bad redirect URL requested, cannot contain #anchor")
            self.path=url
            self.command="GET"
            result=self.do_GETorHEAD(request,response)
            if result:
                if not response.used() or isInclude:
                    # only flush when it is not yet used... (or when something is being included)
                    if not response.used():
                        response.writeHeader()
                    response.forceFlush(self.wfile)  
                self.copyfile(result, self.wfile, False)

#
#   The threading HTTP server.
#   We do all socket handling ourselves, to have maximum control.
#
class ThreadingHTTPServer:

    WEBAPPSDIR = "webapps"
    INDEXPAGES = ["index.html", "index.htm", "index.y"]         # add others if desired

    def __init__(self,HTTPD_PORT, externalPort, bindname, serverURLprefix, debugRequests, precompileYPages, writePageSource):
        log.info( 'Creating server on "%s"' % bindname )
        self.server_address = (bindname, HTTPD_PORT)
        self.server_port=HTTPD_PORT
        self.RequestHandlerClass = MyRequestHandler     # see above
        self.mustShutdown=False
        self.serverURLprefix=''
        self.requestCounter=0
        self.debugRequests=False
        self.precompileYPages = True
        self.writePageSource = False
        self.debugReloading = False
        self.virtualHosts = {}      # maps hostnames to list of web applications
        self.webRoots = {}          # maps hostnames to root web application (or None)
        self.vhostAliases={}        # maps alias to real vhost
        self.useVirtualHosts=True
        self.defaultVirtualHost = None
        import weakref
        self.allWebApps = weakref.WeakValueDictionary()     # maps (vhostname, urlprefix) tuple to web application
        self.setExternalPort(externalPort)
        self._hostname_cache = {}
        self.startTime = time.time()
    
        # make sure serverURLprefix is of the form  "/prefix"
        if serverURLprefix:
            if not serverURLprefix.startswith('/'):
                serverURLprefix='/'+serverURLprefix
            if serverURLprefix.endswith('/'):
                serverURLprefix=serverURLprefix[:-1]
            # global URL prefix for outbound URLs (for running behind proxy)
            self.serverURLprefix=serverURLprefix
        self.debugRequests=debugRequests
        self.precompileYPages = precompileYPages
        self.writePageSource = writePageSource
        
        # determine all modules that are loaded at this point
        self.initialModules = sys.modules.keys()
    
        # read and initialize the plugins, and then the  webapps with their snakelets
        self.loadPluginsAndWebApps()
        
        if serverURLprefix:
            log.debug( "Server URL prefix: "+serverURLprefix )
        log.info( SNAKELETS_VERSION+ " using port %d" % HTTPD_PORT )

    def loadPluginsAndWebApps(self):
        # First read all plugins, the webapps depend on them.
        self.plugins = plugin.PluginRegistry()
        self.plugins.load(self)
        
        # Check if a dirlister plugin is present. If not, install the default.
        if not 'DirLister' in self.plugins.getPluginNames():
            self.plugins.addPlugin(None, DefaultDirListerPlugin() )

        # Now read the webapps. Start with the virtual host config.
        try:
            vhostconfig=__import__(self.WEBAPPSDIR)
            if vhostconfig.ENABLED:
                if vhostconfig.virtualhosts is None or vhostconfig.webroots is None or vhostconfig.defaultvhost is None or vhostconfig.aliases is None:
                    raise ImportError("not everything is configured in the vhost config")
        except ImportError:
            log.error("no correct virtual host config found!")
            log.error("Please read and edit the __init__.py file in the webapps directory.")
            raise InvalidConfigurationException

        if not vhostconfig.ENABLED:
            log.warn("\NOTICE: VirtualHost configuration is NOT enabled.")
            log.warn("Defaulting to loading all available web apps to the current host." )
            vhost=self.server_address[0] or socket.gethostname()
            webapps = [app for app in os.listdir(self.WEBAPPSDIR) if os.path.isdir(os.path.join(self.WEBAPPSDIR, app)) ]
            if 'CVS' in webapps and os.access(os.path.join(self.WEBAPPSDIR, 'CVS','Entries'),os.R_OK):
                webapps.remove('CVS')  # ignore CVS directory
            if '.svn' in webapps and os.access(os.path.join(self.WEBAPPSDIR, '.svn','entries'),os.R_OK):
                webapps.remove('.svn')  # ignore Subversion directory
            vhostconfig.virtualhosts = { vhost: webapps }
            vhostconfig.webroots = {}
            if 'ROOT' in webapps:
                vhostconfig.webroots= { vhost: 'ROOT' }
                webapps.remove('ROOT')
            vhostconfig.aliases = {}
            vhostconfig.defaultvhost = vhost
            self.useVirtualHosts=False

        # do some sanity checks     
        if vhostconfig.defaultvhost not in vhostconfig.virtualhosts:
            raise ValueError("invalid default virtualhost specified: "+vhostconfig.defaultvhost)

        for vhost in vhostconfig.aliases.values():
            if vhost not in vhostconfig.virtualhosts and vhost not in vhostconfig.webroots:
                raise ValueError("invalid vhost specified in aliases: "+vhost)
            if vhost in vhostconfig.aliases:
                raise ValueError("alias cycle: "+vhost)
        
        invalidAliases= [ vhost for vhost in vhostconfig.aliases.keys() if vhost in vhostconfig.virtualhosts or vhost in vhostconfig.webroots ]
        if invalidAliases:
            raise ValueError("aliases defined for true vhosts: "+str(invalidAliases))

        for webroothost in vhostconfig.webroots:
            if webroothost not in vhostconfig.virtualhosts:
                raise ValueError("web root host is not a known virtualhost: "+webroothost)

        self.vhostAliases = vhostconfig.aliases
                
        self.allWebApps.clear()
        self.defaultVirtualHost = ( vhostconfig.defaultvhost, self.externalPort )    # XXX server port is static for now (no multiple connectors)

        webappsAlreadyPrecompiled=[]    # list of webapps whose Ypages have already been precompiled.
        
        # scan regular web applications
        self.virtualHosts.clear()
        for (virtualhost,webapps) in vhostconfig.virtualhosts.iteritems():
            log.info( "Processing virtual host '%s'" % virtualhost )
            if type(webapps) not in (list,tuple):
                raise ValueError("mapping value must be list of webapp names, but it isn't. vhost='%s'" % virtualhost)
                
            self.virtualHosts[virtualhost]=[]
            webapps=list(webapps)
            for webname in webapps:
                log.info( "Loading webapp '%s'" % webname )
                if webapps.count(webname)>1:
                    raise ValueError("Web application '%s' occurs more than once for vhost '%s'" % (webname, virtualhost))
                    
                WA=self.readWebApp(webname, virtualhost, isRoot=False)
                if WA:
                    if self.precompileYPages:
                        if webname not in webappsAlreadyPrecompiled:
                            WA.precompileYPages()
                            webappsAlreadyPrecompiled.append(webname)
                        else:
                            log.debug( "(already precompiled all Ypages)" )
                    log.info( "Got webapp: "+str(WA) )
                    self._registerWebApp(virtualhost, WA, isRoot=False)

        # scan root web applications
        self.webRoots.clear()
        for (virtualhost,webname) in vhostconfig.webroots.iteritems():
            if webname:
                log.info("Processing virtual host '%s' root webapp '%s'" % (virtualhost, webname))
                WA=self.readWebApp(webname, virtualhost, isRoot=True)
                if WA:
                    if self.precompileYPages:
                        if webname not in webappsAlreadyPrecompiled:
                            WA.precompileYPages()
                            webappsAlreadyPrecompiled.append(webname)
                        else:
                            log.debug("(already precompiled all Ypages)")
                    log.debug( "Got webapp: "+str(WA))
                    self._registerWebApp(virtualhost, WA, isRoot=True)

        log.info("Default virtual host: %s:%d" % self.defaultVirtualHost)
        log.info( "%d webapps registered." % len(self.allWebApps))
        if not self.allWebApps:
            print >>sys.stderr,"There are no webapps!"
            raise InvalidConfigurationException


    def _registerWebApp(self, virtualhost, WebApp, isRoot=False):
        if not isRoot:
            self.virtualHosts[virtualhost].append(WebApp)
        else:
            self.webRoots[virtualhost]=WebApp
        self.allWebApps[ (virtualhost, WebApp.getURLprefix() ) ] = WebApp
    

    def readWebApp(self, web, virtualHost, isRoot=False):
        # add the webapps dir to the module search path.
        abspath=os.path.abspath(os.path.join(self.WEBAPPSDIR,web))
        sys.path.append(abspath)
        
        if isRoot:
            url='/'
        else:
            url='/'+web+'/'

        port=self.externalPort  # XXX port is static for now, determined at startup
        
        WA = webapp.createWebApp(abspath, web, url, (virtualHost, port), self)
        if WA:
            log.debug( "WEBAPP "+web+" (%d snakelets )" % len(WA.getSnakelets() ) )
            log.debug(" name = "+WA.getName()[1])
            log.debug("  url = "+WA.getURLprefix())
            return WA
        else:
            log.error("!!! webapp '%s' NOT installed" % web)
            sys.path.remove(abspath)
            return None

    def getWebApp(self, url, virtualhost):
        if not url.startswith(self.serverURLprefix+'/'):
            return None     # server prefix doesn't match

        if not self.useVirtualHosts:
            virtualhost = self.defaultVirtualHost[0]
        else:
            # replace vhost alias by real vhost, if an alias is defined.
            virtualhost = self.vhostAliases.get(virtualhost, virtualhost)

        # go find the webapp that handles this url!
        # only take webapps into account that are connected to this virtualhost
        restrictedToWebApps = self.virtualHosts.get(virtualhost, [])
        restrictedToRootWebApp = self.webRoots.get(virtualhost, None)

        for webapp in restrictedToWebApps:
            if url.startswith(webapp.getURLprefix()):
                if webapp.isEnabled():
                    return webapp
                else:
                    break   # webapp was found, but disabled. Pass on to root webapp.
            
        # fallback to ROOT webapp, if it is enabled
        if restrictedToRootWebApp and restrictedToRootWebApp.isEnabled():
            return restrictedToRootWebApp
        else:
            return None     # nothing suitable found

    def enableWebApp(self, vhost, urlprefix, enabled):
        # enable/disable the webapp for this url prefix
        self.allWebApps[(vhost, urlprefix)].setEnabled(enabled)

    def reloadWebApp(self, vhost, urlprefix):
        # reload the webapp for this url prefix
        numapps=len(self.allWebApps)
        webapp=self.allWebApps[(vhost,urlprefix)]
        webappname=webapp.getName()[0]
        webappid=id(webapp)
        del webapp
        wasRoot=False
        if vhost in self.webRoots:
            wasRoot=self.webRoots[vhost].getName()[0]==webappname
        log.info( "UNLOADING WEBAPP '%s' [%s] id=%08x" % (webappname, vhost, webappid) )
        if self.unloadWebApp(vhost, urlprefix):
            if len(self.allWebApps) != (numapps-1):
                log.warn( "**** WEBAPP '%s' [%s] DIDN'T UNLOAD FULLY ****" % (webappname, vhost))
            WA = self.readWebApp(webappname, vhost, isRoot=wasRoot)
            self._registerWebApp(vhost, WA, isRoot=wasRoot)
            log.info("RELOADED WEBAPP '%s' [%s] id=%08x" % (webappname, vhost, id(WA)))
            return True
        else:
            return False

    def reloadAllModules(self):
        # reload all modules in sys.path, except those loaded when just started (initialModules) 
        for (name,module) in sys.modules.items():
            if module and (module.__name__ not in self.initialModules) and hasattr(module,"__file__"):
                if os.path.dirname(module.__file__) in sys.path:
                    try:
                        log.info("Reloading module "+module.__name__)
                        reload(module)
                    except Exception,x:
                        log.error("Error reloading module %s" % module.__name__)
                        log.error("Error was: "+str(x))

    def clearWebAppCache(self, vhost, urlprefix):
        self.allWebApps[(vhost, urlprefix)].clearCache()

    def unloadWebApp(self, vhost, web):
        webapp=self.allWebApps[(vhost,web)]
        name=os.path.split(webapp.getFileSystemPath())[1]
        modulename="webapps."+name
        
        # count instances of the web app that we're going to unload...
        instances = [wapp for wapp in self.allWebApps.values() if wapp.getName()==webapp.getName() ]
        if len(instances)>1:
            return False
        del instances
    
        for n in sys.modules.keys()[:]:
            if n.startswith(modulename) and type(sys.modules[n]) is types.ModuleType:
                del sys.modules[n]

        if webapp in self.virtualHosts[vhost]:
            self.virtualHosts[vhost].remove(webapp)
        if vhost in self.webRoots and self.webRoots[vhost] is webapp:
            del self.webRoots[vhost]
        try:
            webapp.close()
        except Exception,x:
            log.warn("error during unload: %s",x)
        return True

    def setDebugReloading(self, enabled):
        self.debugReloading=enabled
                
    def getUpTime(self):
        secs=int(time.time()-self.startTime)
        days = secs / (24*3600)
        secs-=days*(24*3600)
        hours=secs/3600
        secs-=hours*3600
        mins=secs/60
        secs-=mins*60
        return (days, hours, mins, secs)

    def getPlugin(self, pluginname):
        return self.plugins.getPlugin(pluginname)
    def getPluginNames(self):
        return self.plugins.getPluginNames()
        
    def getHostName(self, ip):
        # get the FQ hostname that belongs to the specified IP address (and cache it)
        if self._hostname_cache.has_key(ip):
            return self._hostname_cache[ip]
        else:
            x=socket.getfqdn(ip)
            self._hostname_cache[ip]=x
            return x

    def shutdown(self):
        self.mustShutdown=True

    def serve_forever(self):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.socket.listen(100)     # start listening on the socket
        self.mustShutdown=False

        self.plugins.serverStart()      # tell the plugins that the server is starting

        previousReap=time.time()
        while not self.mustShutdown:
            ins,outs,excs=select.select([self],[],[self],10)    # 10 second timeout
            if self in ins:
                self.handle_request()
            if time.time()-previousReap >=30:    # only reap once every 30 seconds or so
                self.reapSessions()
                previousReap=time.time()
        log.debug("Shutting down gracefully")

    def server_close(self):
        self.socket.close()         # stop accepting requests
        print "Closing down webapps..."
        log.info("Closing down webapps...")
        for webapp in self.allWebApps.values():
            log.debug("closing %s",webapp)
            try:
                webapp.close()
            except Exception,x:
                log.warn("Error during closing: %s",x)
                import traceback
                log.warn( "".join(traceback.format_exception(*sys.exc_info())) )
        del self.virtualHosts
        del self.webRoots
        del self.allWebApps
        self.plugins.serverStop()       # tell the plugins that the server has been stopped.

    def fileno(self):
        # interface required for select system call
        return self.socket.fileno()

    def handle_request(self):
        # Handle one request, possibly blocking.
        try:
            request, client_address = self.socket.accept()
        except socket.error:
            return
        try:
            self.process_request(request, client_address)
        except:
            self.logProcessError(client_address)
            try:
                request.shutdown(2)     # apachebench needs this, weird...
                request.close()
            except Exception,x:
                log.warn("Error during closing of connection: %s",x)

    if THREADING_ENABLED:
        def process_request_Thread(self, request, client_address):
            try:
                # Finish one request by instantiating RequestHandlerClass.
                if IS_SSL:
                    tlsConnection = TLSConnection(request)
                    if self.handshake(tlsConnection) == True:
                        self.RequestHandlerClass(tlsConnection, client_address, self)
                        tlsConnection.close()
                else:
                    self.RequestHandlerClass(request, client_address, self)
            except:
                self.logProcessError(client_address)
            # close the request.
            try:
                request.shutdown(2)     # apachebench needs this, weird...
                request.close()
            except Exception,x:
                log.warn("Error during closing of connection: %s",x)
    
        def process_request(self, request, client_address):
            # Start a new thread to process the request.
            t = threading.Thread(target = self.process_request_Thread, args = (request, client_address))
            t.setDaemon (False)
            t.start()
    else:
        # No threading.
        def process_request(self, request, client_address):
            # Finish one request by instantiating RequestHandlerClass.
            if IS_SSL:
                tlsConnection = TLSConnection(request)
                if self.handshake(tlsConnection) == True:
                    self.RequestHandlerClass(tlsConnection, client_address, self)
                    tlsConnection.close()
            else:
                self.RequestHandlerClass(request, client_address, self)
            # close the request.
            try:
                request.shutdown(2)     # apachebench needs this, weird...
                request.close()
            except Exception,x:
                log.warn("Error during closing of connection: %s",x)
        
    def logProcessError(self, client_address):
        log.error("Exception happened during processing of request from %s",client_address)
        (t,v,r)=sys.exc_info()
        log.error("It was: %s; %s", t,v)

    def reapSessions(self):
        # close and delete all web sessions that have timed out.
        for webapp in self.allWebApps.values():
            webapp.sessions.scanSessionTimeouts()

    def setExternalPort(self, externalPort):
        self.externalPort = externalPort or self.server_port
    
    def handshake(self, tlsConnection):
        try:
            tlsConnection.handshakeServer(certChain=certChain,
                                        privateKey=privateKey,
                                        sessionCache=sessionCache)
            tlsConnection.ignoreAbruptClose = True
            return True
        except (SyntaxError, TLSError), error:
            print "Handshake failure:", str(error)
            return False        

    


#
#   Default directory lister plugin.
#   This one is used automatically if no custom dirlister plugin is installed.
#   It's rather simple, it only shows a sorted list of the dirs and the files.
#
class DefaultDirListerPlugin(plugin.DirListerPlugin):
    name='DirLister'
    def listDir(self, filesyspath, urlpath, outputStream):
        f=outputStream
        filelist,dirlist = util.listdir(filesyspath)
        filelist.sort(lambda a, b: cmp(a.lower(), b.lower()))
        dirlist.sort(lambda a, b: cmp(a.lower(), b.lower()))
        f.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n')
        f.write('<html>\n')
        f.write(("<head><title>Directory listing for %s</title></head>\n" % urlpath ) +
                ("<body>\n<h2>Directory listing for %s</h2>\n<hr>\n" % urlpath))
        if urlpath:
            f.write("<p><a href=\"..\">&uarr; parent directory</a>")
        if dirlist:
            f.write("<h4>Directories</h4>\n<ul>\n")
            f.write( '\n'.join( ['<li><a href="%s/">%s</a>' % (urllib.quote(name), name) for name in dirlist ]) )
            f.write("</ul>\n")
        if filelist:
            f.write("<h4>Files</h4>\n<ul>\n")
            f.write( '\n'.join( ['<li><a href="%s">%s</a>' % (urllib.quote(name), name) for name in filelist ]) )
            f.write("</ul>\n")
        else:
            f.write("<p>There are no files in this location.\n")
        f.write("<hr>\n\n<address>Served by Snakelets</address>")
        f.write("\n</body></html>")


#
#   Start everything!
#

def main(HTTPD_PORT=80, externalPort=None, bindname=None, serverURLprefix='', debugRequests=False, precompileYPages=True, writePageSource=False, debugReloadMode=False):

    global log, accesslog
    rootdir=os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    os.chdir(rootdir)
    print "Switched to working directory:",os.getcwd()
    logging.config.fileConfig("logging.cfg")
    log=logging.getLogger("Snakelets.logger")
    accesslog=logging.getLogger("Snakelets.logger.accesslog")
    
    print "Installing stdout/stderr logging adapters."

    class StdoutLogAdapter:
        def __init__(self, name):
            self.log=logging.getLogger(name)
            self._msg=[]
        def __del__(self):
            self.close()
        def write(self, msg):
            self._msg.append(msg)
            if msg.endswith('\n'):
                self.flush()
        def flush(self):
            if self._msg:
                self.log.info("".join(self._msg).rstrip())
                self._msg=[]
        def close(self):
            self.flush()
            del self.log, self._msg

    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout=StdoutLogAdapter("Snakelets.logger.stdout")
        sys.stderr=StdoutLogAdapter("Snakelets.logger.stderr")
    
        print "Server is starting! "+SNAKELETS_VERSION
        log.info("-"*40)
        log.info("Server is starting! "+SNAKELETS_VERSION)
        
        if sendfile:
            log.info("sendfile(2) is available for high performance file serving")
        else:
            log.info("sendfile(2) is NOT available, compatible but slower file serving is used")
        
        if bindname is None:
            bindname=socket.gethostname()
    
        try: 
            httpd=ThreadingHTTPServer(HTTPD_PORT,externalPort,bindname,serverURLprefix,debugRequests,precompileYPages,writePageSource)
            httpd.setDebugReloading(debugReloadMode)
            
            sys.stdout.flush()
            try:
                print "Serving requests."
                httpd.serve_forever()
            except KeyboardInterrupt:
                log.warn("Server got a keyboard interrupt signal")
                    
            log.warn("Server is shutting down.")
            log.warn("-"*40)
            httpd.server_close()
            log.info("Exiting.")
            print "Exiting."
            return
        except (InvalidConfigurationException, webapp.WebAppInitialisationError):
            # exact error has already been logged
            print >>sys.stderr,"Server couldn't start due to errors."
            log.error("Server couldn't start due to errors.")
    finally:
        # restore original stdout/stderr
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout, sys.stderr  = orig_stdout, orig_stderr
    print "The end."


if __name__=="__main__":
    main()

