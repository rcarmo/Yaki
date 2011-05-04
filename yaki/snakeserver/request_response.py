#############################################################################
#
#	$Id: request_response.py,v 1.47 2008/10/12 15:42:16 irmen Exp $
#	HTTP Request / Response stuff
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

from util import ContextContainer
import mycookie
import Cookie
import cgi, urllib
import sys
import codecs
from util import NormalizedHeaderDict
from webform import *


#
#   The REQUEST encapsulation object
#
class Request(object):
    def __init__(self,webapp, pathinfo, query, server, ins):
        self.webapp=webapp  # not a weakref, because a request object is short-lived.
        self.ins=ins
        self.server=server
        self.context=ContextContainer() # only for this request
        self.session=None
        # simulate minimal CGI environment, so we can use the CGI module later
        # to parse the GET/POST requests into a Form object.
        self.env={}
        self._init_query(pathinfo, query)
        self.env['REQUEST_METHOD'] = server.command
        self.env['CONTENT_TYPE'] = server.headers.typeheader or server.headers.type
        self.env['CONTENT_LENGTH'] = server.headers.getheader('content-length') or -1

        co = filter(None, server.headers.getheaders('cookie'))
        if co:
            self.HTTP_COOKIE=', '.join(co)
        else:
            self.HTTP_COOKIE=None
        self.cookies=mycookie.SimpleRequestCookie()
        if self.HTTP_COOKIE:
            self.cookies.load(self.HTTP_COOKIE)
        self.maxPOSTsize=200000  # 200Kbytes 
        self.setEncoding(None)

    def _init_query(self, pathinfo, query):
        # this is called by __init__() but also when constructing
        # a new request object as a result of redirection/inclusion
        self.PATH_INFO=pathinfo
        self.arg=None
        if query:
            possible_query_arg = query.split('&',1)
            if '=' not in possible_query_arg[0]:
                self.arg=possible_query_arg[0]      # query argument without a value ("=") --> self.arg
                if len(possible_query_arg)>1:
                    query=possible_query_arg[1]     # query is the leftovers (without the self.arg part
                else:
                    query=''
        self.QUERY_STRING=self.env['QUERY_STRING'] = query or ""   # still not unquote it!
        # do NOT unquote the query string, because it is composed of multiple elements
        # that have to be unquoted separately (otherwise you may lose the & separator)
        self._PATH_INFO = self.PATH_INFO # store the quoted one
        self._arg = self.arg # store the quoted one
        if self.PATH_INFO:
            self.PATH_INFO=urllib.unquote_plus(self.PATH_INFO)  # finally, unquote it.
        if self.arg:
            self.arg=urllib.unquote_plus(self.arg)  # finally, unquote it.
        self._cgi_form=None

    def getServerSoftware(self):    return self.server.version_string()
    def getSnakeletsVersion(self):  return self.server.snakelets_version
    def getServerIP(self):          return self.server.getServerIP()
    def getServerName(self):        return self.server.getServerName()
    def getRealServerName(self):    return self.server.getRealServerName()
    def getServerProtocol(self):    return self.server.protocol_version
    def getServerPort(self):        return self.server.server.server_port
    def getBaseURL(self):       return self.server.getBaseURL()
    def getPathInfo(self):      return self.PATH_INFO  # unquoted
    def getMethod(self):        return self.env['REQUEST_METHOD']
    def setMethod(self, method): self.env['REQUEST_METHOD']=method
    def getQuery(self):         return self.QUERY_STRING  # unquoted
    def getRequestURL(self):    return self.server.path
    def getRequestURLplain(self): return self.server.path.split('?')[0]
    def getRemoteHost(self):    return self.server.address_string()
    def getRemoteAddr(self):    return self.server.client_address[0]
    def getContentType(self):   return self.env['CONTENT_TYPE']
    def getContentLength(self): return self.env['CONTENT_LENGTH']
    def getUserAgent(self):     return self.server.headers.getheader('user-agent') or ''
    def getReferer(self):       return self.server.headers.getheader('referer') or ''
    def getCookie(self):        return self.HTTP_COOKIE
    def getCookies(self):       return self.cookies
    def clearCookies(self):
        self.HTTP_COOKIE=None
        self.cookies=mycookie.SimpleRequestCookie()
    def getInput(self):         return self.ins
    def getArg(self):           return self.arg
    def setArg(self, arg):      self.arg=arg
    def getWebApp(self):        return self.webapp
    def getRangeStr(self):      return self.server.headers.getheader('range') or ''
    def getRange(self):
        rangeStr=self.getRangeStr()
        if rangeStr:
            # content range is like "bytes=9000-12000" or "bytes=234-"
            t,r = rangeStr.split('=')
            if t.lower()=="bytes":
                frm,to = r.split('-')
                frm = int(frm or 0)
                to = int(to or sys.maxint)
                return frm,to
            else:
                # only supports bytes ranges...
                raise ValueError("only supports range header in BYTES")
        else:
            return None

    def getRealRemoteAddr(self):
        return self.server.headers.get("x-forwarded-for") or self.getRemoteAddr()
    def getAuth(self):              return self.server.headers.getheader('Authorization') or ''
    def getAllHeaders(self):        return self.server.headers
    def getHeader(self, header):    return self.server.headers.getheader(header)  # returns header value, or None
    def getForm(self):
        # return a cached form if it exists (once it has been parsed)
        if self._cgi_form is not None:
            return self._cgi_form
        else:
            try:
                maxlen, cgi.maxlen = cgi.maxlen, self.maxPOSTsize
                try:
                    self._cgi_form = Form(cgi.FieldStorage(fp=self.ins, environ=self.env), self.getEncoding())
                except ValueError,x:
                    raise FormFileUploadError(x)

                if sys.version_info <= (2,6) and self.getMethod()=='POST':
                    # Older versions of the cgi module didn't parse QUERY_STRING if method is POST. 
                    self._cgi_form.parseQueryArgs(self.getQuery())
                self._cgi_form.simplifyValues()
                return self._cgi_form
            finally:
                cgi.maxlen=maxlen
    def getField(self,param,default=''):
        return self.getForm().get(param,default)
    def getParameter(self,param,default=''):
        form=self.getForm()
        if param in form:
            return form[param]
        if hasattr(self.context, param):
            return getattr(self.context, param)
        return default
    def getContext(self):
        return self.context
    def setSession(self, session):
        self.session=session
    def getSession(self):
        return self.session
    def deleteSession(self):
        self.session.destroy()
        self.clearCookies()
    def getSessionContext(self):
        if self.session:
            return self.session.getContext()
        return None
    def setMaxPOSTsize(self, numbytes):
        self.maxPOSTsize=numbytes
    def getMaxPOSTsize(self):
        return self.maxPOSTsize
    def getEncoding(self):
        return self.charEncoding or self.webapp.defaultRequestEncoding
    def setEncoding(self, encoding):
        if self._cgi_form is not None and self.charEncoding != encoding:
            raise ValueError("cannot change encoding after the request data has been accessed")
        self.charEncoding=encoding
    def getFullQueryArgs(self):
        # use the original, quoted strings.
        qa=self._PATH_INFO or ""
        if self.QUERY_STRING or self._arg:
            qa+='?'
        if self._arg:
            qa+=self._arg
            if self.QUERY_STRING:
                qa+='&'
        if self.QUERY_STRING:
            qa+=self.QUERY_STRING
        return qa



#
#   The RESPONSE encapsulation object
#
class Response(object):
    def __init__(self, webapp, server, outs):
        self.webapp=webapp  # not a weakref, because a response object is short-lived.
        self.server=server
        self._outs=self.outs=outs
        self.content_type="text/html"
        self.content_encoding=None
        self.content_length=-1
        self.content_disposition=None
        self.header_written=False
        self.error_sent=False
        self.redirection_performed=False
        self.__being_redirected=False
        self.response_code=200
        self.response_string="OK"
        self.userHeaders=NormalizedHeaderDict()
        self.cookies=Cookie.SimpleCookie()
        self.__outputsstack=[]
    def setContentType(self, type):
        self.content_type=type
    def setContentDisposition(self, disposition):
        self.content_disposition=disposition
    def setContentLength(self, length, force=False):
        if not force and self.content_encoding:
            raise IOError("cannot set content length if a custom output encoding has been specified")
        self.content_length=length
        if self.server:
            self.server.content_length=length
    def getEncoding(self):
        return self.content_encoding
    def setEncoding(self, encoding):
        if self.__being_redirected or self.content_encoding==encoding:
            # We're being used in a redirection/inclusion, or the specified encoding
            # is already set. Do not change the encoding in both cases.
            return
        self.content_encoding=encoding
        if self.content_length>=0:
            raise IOError("cannot set custom output encoding if contentlength has been specified")
        if encoding:
            self.outs=codecs.getwriter(encoding)(self._outs, errors="xmlcharrefreplace")
        else:
            self.outs=self._outs # remove codec
    def forceEncoding(self, encoding):
        # set an encoding. No checks! Danger! Normal usage should be setEncoding.
        self.content_encoding = encoding
    def guessMimeType(self, filename):
        return self.server.guess_type(filename)
    def setHeader(self, header, value):
        self.userHeaders[header]=value
    def getHeader(self, header):
        return self.userHeaders.get(header)
    def setResponse(self, code, msg="Snakelet output follows"):
        self.response_code=code
        self.response_string=msg
    def HTTPredirect(self, URL):
        if self.header_written:
            raise RuntimeError('can not redirect when getOutput() has been called')
        self.setResponse(302) # HTTP 302=redirect (Found)
        self.userHeaders["Location"]=URL
        out=self.getOutput()
        out.write("<html><head><title>Redirection</title></head>\n"
                  "<body><h1>Redirection</h1>\nYou're being <a href=\""+URL+"\">redirected</a>.</body></html>")
        self.setRedirectionDone()
    def writeHeader(self):
        # minimalistic HTTP response header
        if self.header_written:
            raise RuntimeError("header has already been written")
        self.server.send_response(self.response_code, self.response_string)
        contentType=self.content_type
        if self.content_encoding:
            contentType+="; charset="+self.content_encoding
        self.userHeaders["Content-Type"]=contentType
        if self.content_disposition:
            self.userHeaders["Content-Disposition"]=self.content_disposition
        if self.content_length>=0:
            self.userHeaders["Content-Length"]=str(self.content_length)
        for (h,v) in self.userHeaders.iteritems():
            self.server.send_header(h,v)
        for c in self.cookies.values():
            self.server.send_header("Set-Cookie",c.OutputString())
        self.server.end_headers()
        self.header_written=True
    def getOutput(self):
        if self.redirection_performed:
            raise RuntimeError('cannot write after redirect() call')
        if not self.header_written:
            self.writeHeader()
        return self.outs
    def sendError(self, code, message=None):
        if not self.header_written:
            self.error_sent=True
            self.header_written=True
            self.server.send_error(code, message, self.userHeaders)
        else:
            raise RuntimeError("cannot send error after header has been written")
    def getCookies(self):
        return self.cookies
    def setCookie(self, name, value, path=None, domain=None, maxAge=None, comment=None, secure=None):
        self.cookies[name]=value
        self.cookies[name]["version"]=1
        self.cookies[name]["path"]=''
        self.cookies[name]["domain"]=''
        self.cookies[name]["max-age"]=''
        self.cookies[name]["expires"]=''
        self.cookies[name]["comment"]=''
        self.cookies[name]["secure"]=''
        if path: self.cookies[name]["path"]=path
        if domain: self.cookies[name]["domain"]=domain
        if maxAge!=None:
            self.cookies[name]["max-age"]=maxAge  # for modern browsers
            if maxAge>0:
                self.cookies[name]["expires"]=maxAge  # for Internet Explorer
            else:
                # discard cookie, set expires to a time far in the past
                self.cookies[name]["expires"]="Mon, 01-Jan-1900 00:00:00 GMT"  # for Internet Explorer
        if comment: self.cookies[name]["comment"]=comment
        if secure: self.cookies[name]["secure"]=secure
        self.userHeaders["P3P"]="CP='CUR ADM OUR NOR STA NID'"    # P3P compact policy
    def delCookie(self, name, path=None, domain=None, comment=None, secure=None):
        # delete the cookie by setting maxAge to zero.
        self.setCookie(name, "", path, domain, 0, comment, secure)
        
    def setRedirectionDone(self):
        self.__being_redirected=False
        self.redirection_performed=True
    def beingRedirected(self):
        return self.__being_redirected
    def used(self):
        return self.redirection_performed or self.header_written or self.error_sent
    def kill(self):
        self.server.kill()
        self.error_sent=True
    def initiateRedirection(self,url, isInclude=False):
        self.__being_redirected = True
        if self.header_written:
            self.outs.flush()
        else:
            if isInclude:
                self.writeHeader()
            #else:
                # XXX we used to send a Content-Location header, but the handling is inconsistent
                # among the web-browsers. Opera does it "right" (follows 
                # the RFC http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.14
                # but other browsers such as IE/Mozilla/Firefox do NOT follow the RFC.
                # See https://bugzilla.mozilla.org/show_bug.cgi?id=109553
                # So we don't send this header, and all will be right. I hope.
                # self.userHeaders["Content-Location"]=url
    def wasErrorSent(self):
        return self.error_sent
    def YpushOutput(self, output):
        self.__outputsstack.append(self._outs)  # save old output
        self._outs=self.outs=output
    def YpopOutput(self):
        oldOut = self.__outputsstack.pop()
        self._outs=self.outs=oldOut
    def forceFlush(self, stream):   # force response flush to output stream
        out=self.getOutput()
        stream.flush()
        if hasattr(out, 'fileno'):
            if out.fileno()==stream.fileno():
                # using direct stream, we're done
                return
            else:
                del out, stream
                raise IOError("response is a stream but not the socket. Don't know how to handle this. Bail out")
        # we're using a custom output buffer such as a StringIO. Flush that.
        out.seek(0)
        self.server.copyfile(out, stream, not self.__being_redirected)  # don't close when being redirected..
        # now clear the output buffer
        out.seek(0)
        out.truncate()
