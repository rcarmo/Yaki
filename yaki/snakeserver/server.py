#############################################################################
#
#	$Id: server.py,v 1.213 2008/10/16 19:59:34 irmen Exp $
#	The HTTP Server
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import os, time, sys, types, copy, cStringIO, threading, traceback
import urllib, urllib2, socket, select, shutil
import BaseHTTPServer, mimetypes
import logging, logging.config
import util
import webapp

SNAKELETS_VERSION = "Snakelets 1.52-rcarmo"
THREADING_ENABLED = True # False for better debugging, True for multithreaded server.


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

    error_message_format = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html><head><title>Error %(code)d</title></head>
<body>
<h1>Error response</h1>
<p>Code %(code)s: %(explain)s.
<p>Server message: %(message)s.
<p><hr><address>"""+server_version+" Python/"+sys.version.split()[0]+"</address></body></html>"

    # extensions_map contains the mime type definitions.
    extensions_map=mimetypes.types_map.copy()
    extensions_map.update(
      {
        "": "text/plain", # Default, *must* be present
        ".mp3"  : "audio/mpeg",
        ".m3u"  : "audio/x-mpegurl",
        ".m4a"  : "audio/mp4",
        ".m4p"  : "audio/mp4",
        ".ogg"  : "application/ogg",
        ".y"    : "text/html",
        ".py"   : "text/plain",
        ".cod"  : "application/vnd.rim.cod",
        ".sis"  : "application/vnd.symbian.install",
        ".sisx" : "application/vnd.symbian.install",
        ".jar"  : "application/java-archive",
        ".jad"  : "text/vnd.sun.j2me.app-descriptor",
        ".class": "application/x-java-class",
        ".gz"   : "application/x-gzip",
        ".bzip" : "application/x-bzip2",     # not sure
        ".bz2"  : "application/x-bzip2",     # not sure
        ".odb"  : "application/vnd.oasis.opendocument.database",
        ".tgz"  : "application/x-gzip-tar",   # not sure
        ".manifest"  : "text/cache-manifest", # iOS
        ".odc"  : "application/vnd.oasis.opendocument.chart",
        ".odf"  : "application/vnd.oasis.opendocument.formula",
        ".odg"  : "application/vnd.oasis.opendocument.graphics",
        ".odi"  : "application/vnd.oasis.opendocument.image",
        ".odm"  : "application/vnd.oasis.opendocument.text-master",
        ".odp"  : "application/vnd.oasis.opendocument.presentation",
        ".ods"  : "application/vnd.oasis.opendocument.spreadsheet",
        ".odt"  : "application/vnd.oasis.opendocument.text",
        ".otg"  : "application/vnd.oasis.opendocument.graphics-template",
        ".oth"  : "application/vnd.oasis.opendocument.text-web",
        ".otp"  : "application/vnd.oasis.opendocument.presentation-template",
        ".ots"  : "application/vnd.oasis.opendocument.spreadsheet-template",
        ".ott"  : "application/vnd.oasis.opendocument.text-template",
        ".stc"  : "application/vnd.sun.xml.calc.template",
        ".std"  : "application/vnd.sun.xml.draw.template",
        ".sti"  : "application/vnd.sun.xml.impress.template",
        ".stw"  : "application/vnd.sun.xml.writer.template",
        ".sxc"  : "application/vnd.sun.xml.calc",
        ".sxd"  : "application/vnd.sun.xml.draw",
        ".sxg"  : "application/vnd.sun.xml.writer.global",
        ".sxi"  : "application/vnd.sun.xml.impress",
        ".sxm"  : "application/vnd.sun.xml.math",
        ".sxw"  : "application/vnd.sun.xml.writer",
        ".7z"   : "application/x-7z-compressed",
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
            log.debug("Socket error during flush: "+str(x))
        if self.raw_requestline:    # only postprocessing of real requests
            try:
                self.processTimeCPU = time.clock() - self.startTimeCPU
                self.processTimeReal = time.time() - self.startTimeReal
                # ... do something with process time?
                if self.server.debugRequests:
                    log.debug( "<<<<< REQUEST TOOK: %d msec. CPU, %d msec. real, HTTP RESPONSE=%d" % ( int( self.processTimeCPU * 1000), int( self.processTimeReal * 1000) , self.response_code ) )
                self.logRequestInfo()
            except Exception,x:
                log.error("Error during finish: %s",x)

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
            format='%s - - [%s] "%s" %s %s "%s" "%s" %f %f'
            useragent=self.headers.getheader('user-agent') or '-'
            referer=self.headers.getheader('referer') or '-'
            size=str(self.content_length) or '-'
            args=( self.address_string(), self.log_date_time_string(), self.raw_requestline.strip(), str(self.response_code) or '?', size, referer, useragent, self.processTimeCPU, self.processTimeReal )
            accesslog.info( format % args )
        # send out notification packet
        self.server.sendEvent("%d %s %s %s %f %f" % (self.response_code, self.raw_requestline.strip().split(' ')[1], referer, size, self.processTimeCPU, self.processTimeReal ))

    def do_GETorHEAD(self, passthroughRequest=None, passthroughResponse=None):
        # common code for GET and HEAD requests. (supports scripts / snakelets)
        web=self.server.getWebApp(self.path, self.virtualhost)
        if not web:
            web = self.server.getWebApp(self.path+'/', self.virtualhost, False)
            if web:
                return self.redirectToWebappWithSlash(passthroughResponse)
            else:
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

        isphysdir = os.path.isdir(fspath)
        if realpath.endswith('/'):  # a directory is requested!
            found=False
            if isphysdir:
                # It is an existing dir on the filesystem.
                # Work trough the configured index pages.
                for index in web.indexPages:
                    indexf = os.path.join(fspath, index)
                    if os.path.exists(indexf):     # search a file that matches
                        fspath = indexf
                        self.path=realpath+index
                        if query:
                            self.path+="?"+query
                        found=True
                        break
            if not found:
                # It is a non-existing pysical dir, or there is no index page in the dir.
                # Try the magic index.sn snakelet instead.
                if web._have_index_snakelet(web._getPath(realpath),"index.sn"):
                    self.path=realpath+"index.sn" # run the index snakelet
                    if query:
                        self.path+="?"+query
                else:
                    # no index page or snakelet found, just a directory then.
                    # but only list it if it really exists.
                    if isphysdir:
                        self.path=realpath # 'forget' query args
                        return self.list_directory(web,fspath,passthroughResponse)
        else:
            if isphysdir and not query:
                # path is a directory but doesn't end with '/', so send a redirect to the proper URL.
                return self._redirectToProperDirectoryURL(urllib.unquote(self.path), passthroughResponse)

        # check if the document is allowed to be served
        if not web.allowDocument(self.path):
            if not passthroughResponse or not passthroughResponse.used():
                log.debug("404 because webapp doesn't allow loading "+self.path )
                self.send_error(404)    # not 403 forbidden..! that would let the 'hacker' know that this file *does* exist
            else:
                passthroughResponse.getOutput().write("No permission (by server config) to view document: "+realpath)
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
        except webapp.TimeoutPageNotFound,x:
            log.debug("500 because timeout page does not exist: "+fspath)
            # process cookie header. This is used to clear the session cookie
            headers={}
            if x.cookie:
                headers["Set-Cookie"]=x.cookie.OutputString()
            self.send_error(500,"the configured session-timeout page could not be found",userHeaders=headers)
        except webapp.NotHandled:
            if not passthroughResponse or not passthroughResponse.used():
                log.debug("404 because file does not exist: "+fspath)
                self.send_error(404)
            else:
                # we're part of another request (included) so we can no longer return a HTTP status error...
                passthroughResponse.getOutput().write("Error on Page; Referenced URL not handled: "+realpath)


    def handleIfModifiedSince(self, etag, lmod):
        # Checks and handles the if-modified-since etc headers
        # If the check is positive (i.e. the resource is NOT modified),
        # returns a 304 status and True ("handled").
        # Otherwise, does nothing, and returns False ("not handled").
        IfModifiedSince=self.headers.get("If-Modified-Since",'')
        IfNoneMatch=self.headers.get("If-None-Match",'')
        IfMatch=self.headers.get("If-Match",'')
        if IfModifiedSince or IfNoneMatch or IfMatch:
            # do special stuff (check if 304 can be returned)
            index=IfModifiedSince.find(';') # strip off IE-shit
            if index>=0:
                IfModifiedSince=IfModifiedSince[:index]
            # check lmod
            if lmod!=IfModifiedSince:
                return False
            # check if-none-match
            if IfNoneMatch and IfNoneMatch!='*':
                if etag not in [tag.strip() for tag in IfNoneMatch.split(',')]:
                    return False
            # check if-match
            if IfMatch:
                if IfMatch=='*' or etag in [tag.strip() for tag in IfMatch.split(',')]:
                    return False
            self.send_response(304) # resource wasn't modified, so return 304 not modified.
            self.send_header("ETag", etag)
            self.end_headers()
            return True             # we handled this request.
        return False

# Enable this for header debugging:
#    def send_header(self, header, value):
#        log.debug(">>> HEADER: %s=%s" %(header,value) )
#        BaseHTTPServer.BaseHTTPRequestHandler.send_header(self, header, value)

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
            f = cStringIO.StringIO()
            self.server.listDir(physicalpath, path, f)
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

    def redirectToWebappWithSlash(self, passthroughResponse):
        newpath=self.getBaseURL()+self.path+'/'     # for instance http://host/test --> http://host/test/
        f=cStringIO.StringIO()
        f.write("<html><head><title>Redirection</title></head>\n"
                "<body>You're being redirected <a href=\""+newpath+"/\">to the application</a>.</body></html>")
        if not passthroughResponse or not passthroughResponse.used():
            self.send_response(302, "Document moved")
            self.send_header("Content-type","text/html")
            path=self.getBaseURL()+self.path+'/'
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
                log.debug("Socket error during copyfile: "+str(x))
        try:
            outputfile.flush()
        except socket.error,x:
            log.debug("Socket error during copyfile flush: "+str(x))
            # ... just ignore this error.
        if closeSource:
            source.close()

    def address_string(self):
        # override the base version that looks up the FQ hostname.
        # we just stick with the IP address...
        # ...and even take the real IP adress if we are proxied by Apache.
        host, port = self.client_address
        realhost=self.headers.get("x-forwarded-for") or host
        realhost = str(realhost)
        # replace IPv6 prefix if unnecessary
        realhost = realhost.replace('::ffff:', '')
        return realhost

    def include(self, url, request, response):
        # read the other URL and write the result to the output stream.
        # Perform this in a clone of our current request handler object.
        response.initiateRedirection(url, isInclude=True)
        handler=copy.copy(self)
        handler.doRedirect(url, request, response, True)

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
class ThreadingHTTPServer(object):

    WEBAPPSDIR = "webapps"
    USERLIBSDIR = "userlibs"
    INDEXPAGES = ["index.y", "index.html", "index.htm"]         # add others if desired, in search order

    __version__= SNAKELETS_VERSION

    def __init__(self,HTTPD_PORT, externalPort, bindname, serverURLprefix, debugRequests, precompileYPages, writePageSource, escrow=None, monitor=None):
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
        self.virtualHosts = {}      # maps hostnames to list of web applications
        self.webRoots = {}          # maps hostnames to root web application (or None)
        self.vhostAliases={}        # maps alias to real vhost
        self.webappStatus={}        # maps webapp name to status ('ok', 'error'...)
        self.useVirtualHosts=True
        self.defaultVirtualHost = None
        import weakref
        self.allWebApps = weakref.WeakValueDictionary()     # maps (vhostname, urlprefix) tuple to web application
        self.setExternalPort(externalPort)
        self._hostname_cache = {}
        self.escrow = escrow
        self.monitorAddress = monitor
        self.startTime = time.time()
        self.configuredWebApps={}   # maps vhost->webapp name 

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

        # prepend the userlibs directory to the module search path
        # this way we make sure we can override obsolete OS libs
        abspath=os.path.abspath(self.USERLIBSDIR)
        sys.path.insert(1,abspath)

        # create the server socket
        self.createServerSocket()

        # create the UDP socket for sending events
        if monitor:
          self.monitor = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        else:
          self.monitor = None

        # read and initialize the  webapps with their snakelets
        self.loadWebApps()

        if serverURLprefix:
            log.debug( "Server URL prefix: "+serverURLprefix )
        log.info( SNAKELETS_VERSION+ " using port %d" % HTTPD_PORT )

    def sendEvent(self, buffer):
      if self.monitor:
        self.monitor.sendto(buffer,self.monitorAddress)

    def _listAvailableWebapps(self, enabledWebapps):
        webapps=[app for app in os.listdir(self.WEBAPPSDIR) if os.path.isdir(os.path.join(self.WEBAPPSDIR, app)) ]
        # ignore certain directories:
        for ingoredir in ['CVS', '.svn']:
            if ingoredir in webapps:
                webapps.remove(ingoredir)
        if "*" in enabledWebapps: 
            return webapps     # wildcard, return everything
        else:
            return [webapp for webapp in webapps if webapp in enabledWebapps]

    def loadWebApps(self):
        try:
            vhostconfig=__import__(self.WEBAPPSDIR)
            if vhostconfig.ENABLED:
                if vhostconfig.virtualhosts is None or vhostconfig.webroots is None or vhostconfig.defaultvhost is None or vhostconfig.aliases is None:
                    raise ImportError("not everything is configured in the vhost config")
        except ImportError:
            log.error("no correct virtual host config found!")
            log.error("Please read and edit the __init__.py file in the webapps directory.")
            raise InvalidConfigurationException("no correct vhost config found")

        if not vhostconfig.ENABLED:
            log.warn("NOTICE: VirtualHost configuration is NOT enabled.")
            log.warn("Defaulting to loading all available web apps to the current host." )
            vhost=self.server_address[0] or socket.gethostname()
            webapps = self._listAvailableWebapps(vhostconfig.defaultenabledwebapps)
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

                if virtualhost not in self.configuredWebApps:
                    self.configuredWebApps[virtualhost]=[]
                self.configuredWebApps[virtualhost].append(webname)
                    
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
                else:
                    raise InvalidConfigurationException("WA didn't initialize")

        # scan root web applications
        self.webRoots.clear()
        for (virtualhost,webname) in vhostconfig.webroots.iteritems():
            if webname:
                log.info("Processing virtual host '%s' root webapp '%s'" % (virtualhost, webname))
                if webname in vhostconfig.virtualhosts[virtualhost]:
                    raise ValueError("Web application '%s' occurs both as normal and as ROOT webapp for vhost '%s'" % (webname, virtualhost))

                if virtualhost not in self.configuredWebApps:
                    self.configuredWebApps[virtualhost]=[]
                self.configuredWebApps[virtualhost].append(webname)

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
            raise InvalidConfigurationException("there are no webapps")


    def _registerWebApp(self, virtualhost, WebApp, isRoot=False):
        if not isRoot:
            self.virtualHosts[virtualhost].append(WebApp)
        else:
            self.webRoots[virtualhost]=WebApp
        self.allWebApps[ (virtualhost, WebApp.getURLprefix() ) ] = WebApp


    def readWebApp(self, web, virtualHost, isRoot=False):
        # add the webapp's directory to the module search path.
        abspath=os.path.abspath(os.path.join(self.WEBAPPSDIR,web))
        sys.path.append(abspath)

        if isRoot:
            url='/'
        else:
            url='/'+web+'/'

        port=self.externalPort  # XXX port is static for now, determined at startup
        WA=None
        try:
            WA = webapp.createWebApp(abspath, web, url, (virtualHost, port), self)
        except Exception,x:
            log.error("Error creating webapp: "+str(x))
            log.error(traceback.format_exc())
            return None
        else:
            if WA:
                log.debug( "WEBAPP "+web+" (%d snakelets )" % len(WA.getSnakelets() ) )
                log.debug(" name = "+WA.getName()[1])
                log.debug("  url = "+WA.getURLprefix())
                if WA.sharedSession:
                    msg=WA.getName()[0]+" shares the session with other webapps. Possible security problem!"
                    log.warn(msg)
                    print "Warning:",msg
                self.webappStatus[web] = 'ok'
                return WA
            else:
                log.error("!!! webapp '%s' NOT installed" % web)
                self.webappStatus[web] = 'error'
                sys.path.remove(abspath)
                return None

    def getWebApp(self, url, virtualhost, includingRoot=True):
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
        if includingRoot and restrictedToRootWebApp and restrictedToRootWebApp.isEnabled():
            return restrictedToRootWebApp
        else:
            return None     # nothing suitable found

    def enableWebApp(self, vhost, urlprefix, enabled):
        # enable/disable the webapp for this url prefix
        self.allWebApps[(vhost, urlprefix)].setEnabled(enabled)

    def reloadWebApp(self, vhost, urlprefix, webappname=None):
        # reload the webapp for this url prefix
        numapps=len(self.allWebApps)
        try:
            webapp=self.allWebApps[(vhost,urlprefix)]
        except KeyError:
            # webapp has not been loaded
            wasRoot=False # XXX what about when it was the root webapp??
        else:
            # unload existing webapp
            webappname=webapp.getName()[0]
            webappid=id(webapp)
            del webapp # required for later ref checking
            wasRoot=False
            if vhost in self.webRoots:
                wasRoot=self.webRoots[vhost].getName()[0]==webappname
            log.info( "UNLOADING WEBAPP '%s' [%s] id=%08x" % (webappname, vhost, webappid) )
            if self.unloadWebApp(vhost, urlprefix):
                if len(self.allWebApps) != (numapps-1):
                    log.warn( "**** WEBAPP '%s' [%s] DIDN'T UNLOAD FULLY ****" % (webappname, vhost))
            else:
                return False
        # reload the webapp
        WA = self.readWebApp(webappname, vhost, isRoot=wasRoot)
        if WA:
            self._registerWebApp(vhost, WA, isRoot=wasRoot)
            log.info("RELOADED WEBAPP '%s' [%s] id=%08x" % (webappname, vhost, id(WA)))
            return True
        else:
            log.warn("FAILED TO RELOAD WEBAPP '%s' [%s]" % (webappname, vhost))
            return False

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

    def removeSharedSession(self, session, vhost, skipwebapp):
        for webapp in self.virtualHosts[vhost]:
            if webapp.sharedSession and webapp.getName()[0]!=skipwebapp:
                webapp._deleteSession(session,checkShared=False)
        if vhost in self.webRoots:
            rootapp=self.webRoots[vhost]
            if rootapp.sharedSession and rootapp.getName()[0]!=skipwebapp:
                rootapp._deleteSession(session,checkShared=False)


    def registerSession(self, webapp, session):
        sessID=session.getID()
        if webapp.sharedSession:
            # register the session with all other webapps that have a shared session
            vhost=webapp.getVirtualHost()[0]
            for wa in self.virtualHosts[vhost]:
                if wa.sharedSession:   # this also includes the webapp itself!
                    wa.sessions[sessID]=session
            if vhost in self.webRoots:
                rootapp=self.webRoots[vhost]
                if rootapp.sharedSession:
                    rootapp.sessions[sessID]=session
        else:
            webapp.sessions[sessID]=session

    def getUpTime(self):
        secs=int(time.time()-self.startTime)
        days = secs / (24*3600)
        secs-=days*(24*3600)
        hours=secs/3600
        secs-=hours*3600
        mins=secs/60
        secs-=mins*60
        return (days, hours, mins, secs)

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

    def createServerSocket(self):
        global privilegedObjects
        self.socket = privilegedObjects.get("socket")
        if self.socket is None:
            log.info("creating new server socket")
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.server_address)
            self.socket.listen(100)     # start listening on the socket
        else:
            log.info("got privileged socket object")


    def serve_forever(self):
        self.mustShutdown=False
        previousReap=time.time()
        while not self.mustShutdown:
            ins,outs,excs=select.select([self],[],[self],5)    # 5 second timeout
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
                log.debug("Error during closing of connection: %s",x)

    if THREADING_ENABLED:
        def process_request_Thread(self, request, client_address):
            try:
                # Finish one request by instantiating RequestHandlerClass.
                self.RequestHandlerClass(request, client_address, self)
            except:
                self.logProcessError(client_address)
            # close the request.
            try:
                request.shutdown(2)     # apachebench needs this, weird...
                request.close()
            except Exception,x:
                log.debug("Error during closing of connection: %s",x)

        def process_request(self, request, client_address):
            # Start a new thread to process the request.
            t = threading.Thread(target = self.process_request_Thread, args = (request, client_address))
            t.setDaemon (False)
            t.start()
    else:
        # No threading.
        def process_request(self, request, client_address):
            # Finish one request by instantiating RequestHandlerClass.
            self.RequestHandlerClass(request, client_address, self)
            # close the request.
            try:
                request.shutdown(2)     # apachebench needs this, weird...
                request.close()
            except Exception,x:
                log.debug("Error during closing of connection: %s",x)

    def logProcessError(self, client_address):
        log.error("Exception happened during processing of request from %s",client_address)
        (t,v,r)=sys.exc_info()
        log.error("It was: %s; %s", t,v)
        import traceback
        err= "".join(traceback.format_exception(t,v,r))
        log.error("Traceback: "+err)


    def reapSessions(self):
        # close and delete all web sessions that have timed out.
        for webapp in self.allWebApps.values():
            webapp.sessions.scanSessionTimeouts()

    def setExternalPort(self, externalPort):
        self.externalPort = externalPort or self.server_port

    def listDir(self, filesyspath, urlpath, out):
        def formatDir(name, stats, comment, idx):
            trclass= ("even","odd") [idx%2]
            return '<tr class="%s"><td><a href="%s/">%s</a></td><td>%s</td><td>%s</td></tr>\n' % (trclass, urllib.quote(name), name,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats.st_mtime) ), comment or "" )
        def formatFile(name, stats, comment, idx):
            trclass= ("even","odd") [idx%2]
            kb,rest=divmod(stats.st_size, 1024)
            if rest:
                kb+=1
            return '<tr class="%s"><td><a href="%s">%s</a></td><td>%s</td><td>%d k</td><td>%s</td></tr>\n' % (trclass, urllib.quote(name), name,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats.st_mtime) ), kb, comment or "" )
        filelist,dirlist = util.listdir(filesyspath)
        filelist.sort(lambda a, b: cmp(a.lower(), b.lower()))
        dirlist.sort(lambda a, b: cmp(a.lower(), b.lower()))
        import ConfigParser
        indexFileName=".snindex"
        cp=ConfigParser.ConfigParser()
        cp.read(os.path.join(filesyspath, indexFileName))
        if cp.has_section("filedescriptions"):
            fileComments=dict(cp.items("filedescriptions"))
        else:
            fileComments={}
        if cp.has_section("hidden"):
            hiddenFiles=dict(cp.items("hidden"))
        else:
            hiddenFiles={}
        hiddenFiles[indexFileName]=None  # always hide the index data file

        out.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n')
        out.write('<html><head>')
        out.write("<title>Directory listing for %s</title>" % urlpath )
        out.write("""
<style type="text/css">
<!--
body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; background-color: #F0FFFF; color: black; }
table { border: none; border-spacing: 1px; margin-bottom: 2ex; margin-left: 2ex; }
h1 { font-size: 14pt; }
a { color: navy; }
a:visited {color: purple; }
a:hover {color: blue; background-color: #c0d0d0;}
td,th {  text-align: left;  border: none; padding: 2px; padding-right: 5ex;}
th.name { width: 30ex; }
tr.even { background-color: #e0f0f0; }
tr.odd { background-color: #e8f8f8; }
table caption { font-size: 12pt; font-weight: bold; font-style: italic; text-align: left; }
-->
</style>""")
        out.write("\n<body><h1>Directory listing for %s</h1>" % urlpath)
        if urlpath:
            out.write("<p><a href=\"..\">&uarr; parent directory</a>")
        if dirlist:
            out.write('\n<table><caption>Directories</caption><tr><th class="name">Directory name</th><th>Last modified</th><th>Comment</th></tr>\n')
            idx=0
            for name in dirlist:
                if name in hiddenFiles:
                    continue
                idx+=1
                stats=os.stat(os.path.join(filesyspath, name))
                out.write( formatDir(name,stats,fileComments.get(name), idx) )
            out.write("</table>\n")
        if filelist:
            out.write('<table><caption>Files</caption><tr><th class="name">File name</th><th>Last modified</th><th>Size</th><th>Comment</th></tr>\n')
            idx=0
            for name in filelist:
                if name in hiddenFiles:
                    continue
                idx+=1
                stats=os.stat(os.path.join(filesyspath, name))
                out.write( formatFile(name,stats,fileComments.get(name),idx) )
            out.write("</table>\n")
        else:
            out.write("<p>There are no files in this location.\n")
        out.write("<br><address>"+self.__version__+"</address>")
        out.write("\n</body></html>")


def lowerPrivileges(userName, groupName):
    if userName or groupName:
        print "Changing user and group to %s:%s" % (userName,groupName)
    util.changeUserAndGroup(userName, groupName)
    util.printCurrentUserAndGroupInfo()
    try:
        if hasattr(os, "umask"):
            os.umask(027)
    except Exception,x:
        print "Problem setting umask: ",x


privilegedObjects = {}

def createPrivilegedObjects(sock_bindname, sock_port):
    # create server socket
    global privilegedObjects
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind( (sock_bindname, sock_port) )
    sock.listen(100)     # start listening on the socket
    privilegedObjects["socket"]=sock


#
#   Start everything!
#
def main(HTTPD_PORT=80, externalPort=None, bindname=None, serverURLprefix='', debugRequests=False,
         precompileYPages=True, writePageSource=False, serverRootDir=None, runAsUser=None, runAsGroup=None, escrow=None, monitor=None):
    global log, accesslog, privilegedObjects

    if not os.path.isfile("logging.cfg"):
    	raise IOError("logging configuration file not found in current directory: logging.cfg")
    logging.config.fileConfig("logging.cfg")
    log=logging.getLogger("Snakelets.logger")
    accesslog=logging.getLogger("Snakelets.logger.accesslog")

    if bindname is None:
        bindname=socket.gethostname()
    if runAsUser or runAsGroup:
        createPrivilegedObjects(bindname, HTTPD_PORT)
        lowerPrivileges(runAsUser, runAsGroup)

    cur_id=util.getCurrentUserAndGroupId()
    if not cur_id:
        log.warning("Unable to query current user id.")
    elif cur_id[0]==0 or cur_id[1]==0:
        raise OSError("Refuses to run as root")

    if serverRootDir:
        os.chdir(serverRootDir)
    log.info("Server root directory: %s" % os.getcwd())
    if escrow:
      log.info("Password key escrow mechanism initialized.")

    class StdoutLogAdapter(object):
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
        log.info("-"*40)
        log.info("Server is starting! "+SNAKELETS_VERSION)

        if sendfile:
            log.info("sendfile(2) is available for high performance file serving")
        else:
            log.info("sendfile(2) is NOT available, compatible but slower file serving is used")

        try:
            httpd=ThreadingHTTPServer(HTTPD_PORT,externalPort,bindname,serverURLprefix,debugRequests,precompileYPages,writePageSource,escrow=escrow,monitor=monitor)

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
            print >>sys.stderr,"Server couldn't start due to errors. (see log)"
            log.error("Server couldn't start due to errors.")
    finally:
        # restore original stdout/stderr
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout, sys.stderr  = orig_stdout, orig_stderr
    log.info("Stopped.")

if __name__=="__main__":
    main()

