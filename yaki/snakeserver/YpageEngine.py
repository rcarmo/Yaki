#############################################################################
#
#	$Id: YpageEngine.py,v 1.79 2006/05/25 17:23:18 irmen Exp $
#	Ypage compilation and execution
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

#
#   This is the Ypage compilation and execution engine.
#
#   It takes care of loading and compiling the Ypage files,
#   and executing them when the page is requested.
#   The compiled pages are cached (in memory).
#   Pages are recompiled if their file modification time
#   is newer than the cached entry's time.
#

import os, time, glob, cStringIO
import imp, sys, weakref, threading
import urlparse,cgi
import codecs
from ypage.compiler import PageCompiler, CompilerError
from snakelet import Snakelet
import httpauth
import logging

log=logging.getLogger("Snakelets.logger")


PAGE_SOURCE_OUTPUTDIR = "tmp"


class YpageEngine(object):

    import string
    ALLOWED_MODULE_CHARS=string.ascii_letters+string.digits+"_"
    MODULE_PREFIX = "Ypage_"

    def __init__(self, name, vhost, writePageSource):
        self.cache = {}     # maps names to bytecode modules
        self.name=name
        self.writePageSource=writePageSource
        if self.writePageSource:
            if not os.path.isdir(PAGE_SOURCE_OUTPUTDIR):
                raise IOError("cannot access page source output dir; "+PAGE_SOURCE_OUTPUTDIR)

            self.pageSourceOutputDir=os.path.join(PAGE_SOURCE_OUTPUTDIR, vhost)
            if not os.path.isdir(self.pageSourceOutputDir):
                os.mkdir(self.pageSourceOutputDir)
            log.info( "Erasing old page sources from "+self.pageSourceOutputDir )
            prefix=self.createPageModuleName("")+'*'
            for f in glob.glob(os.path.join(self.pageSourceOutputDir, prefix)):
                os.remove(f)
        self.lock=threading.Lock()

    def clearCache(self):
        self.lock.acquire()
        try:
            self.cache.clear()
        finally:
            self.lock.release()

    def loadPage(self, pageFile, pageName, webapp, pageTemplateArgs=None):
        # pageFile is the full path name to the file on disk.
        # We could have determined that ourselves here (using webapp.getFullPath)
        # but the webapp already needed it and so we just pass it in.

        (_ignore, _ignore, pageName, pageArgs, _ignore) = urlparse.urlsplit(pageName)
        if pageArgs:
            # pageArgs can be supplied ONLY as part of a template specification.
            pageFile=webapp.getFullPath(pageName)
            pageArgs=dict(cgi.parse_qsl(pageArgs))
            pageArgs.update(pageTemplateArgs or {})
        else:
            pageArgs=pageTemplateArgs

        pageModule = self.createPageModuleName(pageName)

        try:
            try:
                self.lock.acquire() # thread locking to avoid concurrent compiles
                mustCompile=True
                if pageModule in self.cache:
                    compiledPageModule = self.cache[pageModule]
                    mustCompile = os.path.getmtime(pageFile) >= compiledPageModule.__mtime__

                if mustCompile:
                    compiledPageModule=self.compilePageModule(pageFile, pageName, pageModule,
                        webapp.getDocRootPath(), webapp.defaultOutputEncoding, webapp.defaultPageTemplate)
                    compiledPageModule.__mtime__ = time.time()
                    self.cache[pageModule] = compiledPageModule
                #else:
                #   log.debug("page found in cache")
            finally:
                self.lock.release()

            # instantiate page object
            # notice that a new instance is created for each request... not too efficient :-(
            return compiledPageModule.Page(pageName, weakref.ref(webapp), pageArgs or {})

        except CompilerError,x:
            #import traceback
            #log.error("ERROR IN LOADPAGE!  "+unicode(x))
            #log.error( "\n".join(traceback.format_exception(*sys.exc_info())) )
            xmsg = str(x)
            del x
            raise CompilerError(xmsg) # +" (in generated source from Ypage: "+pageName+")")

    def compilePageModule(self, pageFile, pageName, pageModule, docrootPath, defaultOutputEncoding=None, defaultPageTemplate=None):
        starttime=time.clock()
        log.debug("parsing ypage \"%s\"... " %  pageName)
        pythonSource = PageCompiler().compilePage(pageFile, docrootPath, defaultOutputEncoding, defaultPageTemplate)
        if self.writePageSource:
            sourcefile=os.path.join(self.pageSourceOutputDir, pageModule+".py")
            f=open(sourcefile,"wb")
            f.write(pythonSource)
            f.close()
            log.debug("Page source written to "+sourcefile)
        log.debug("compiling...")
        sourcename=os.path.splitext(pageName)[0] # strip the .y suffix
        sourcename=sourcename.replace("/","_").replace("\\","_")
        sourcename = "<Ypage_code_of_%s>" % sourcename
        sourcecode = compile(pythonSource, sourcename, 'exec')
        module = imp.new_module(pageModule)
        exec sourcecode in module.__dict__      # this exec is safe because we execute only code generated by us
        duration=(time.clock()-starttime)*1000
        if duration<1:
            duration=1
        log.debug("done (%d ms, %d lines/sec)" % (duration, module.sourcelines*1000.0/duration ) )
        return module

    def runPage(self, page, _request, _response, defaultOutputEncoding):
        output=cStringIO.StringIO()
        if _response.beingRedirected():
            # we're being used in a redirected/included page. Use previous encoding (if any).
            outputEncoding=_response.getEncoding() or page.getPageEncoding() or defaultOutputEncoding
        else:
            outputEncoding = page.getPageEncoding() or defaultOutputEncoding
        if outputEncoding:
            output=codecs.getwriter(outputEncoding) (output, errors="xmlcharrefreplace")
            _response.forceEncoding(outputEncoding) # make sure correct response header is generated
        _response.YpushOutput(output)        # replace socket output stream by stringio
        page.createOutput(output,_request,_response)    # run the actual page
        _response.YpopOutput()               # switch back to previous output
        output.flush()
        return output, outputEncoding, page.getPageContentTypeAndDisposition()

    def createEncodedString(self, unicodetext, page, response, defaultOutputEncoding):
        if page:
            outputEncoding = response.getEncoding() or page.getPageEncoding() or defaultOutputEncoding
        else:
            outputEncoding = response.getEncoding() or defaultOutputEncoding
        if outputEncoding:
            return unicodetext.encode(outputEncoding, "xmlcharrefreplace"), outputEncoding
        else:
            raise UnicodeError("no output encoding specified")

    def createPageModuleName(self, pageName):
        # returns a unique and valid module name for the compiled ypage
        pageName=pageName.replace('/','__').replace('\\','__')
        result=[self.name+'_']
        for c in pageName:
            if c in self.ALLOWED_MODULE_CHARS:
                result.append(c)
            else:
                result.append('_')
        return self.MODULE_PREFIX + ''.join(result)

    def addPageVars(self, page, webapp, request, response):
        # Add some shortcut attributes to the ypage.
        # (this can be done because we have a new page instance for every request).
        page.Request = request
        page.RequestCtx = request.getContext()
        page.ApplicationCtx = webapp.context
        page.WebApp = weakref.proxy(webapp)
        page.URLprefix = webapp.getURLprefix()
        page.Assetprefix = webapp.getAssetprefix()
        page.User=page.SessionCtx=None
        if page.requiresSession() != Snakelet.SESSION_NOT_NEEDED:
            session=webapp.addSessionCookie(request,response, page.requiresSession()!=Snakelet.SESSION_DONTCREATE)
            if session:
                page.SessionCtx=session.getContext()
                page.User=session.getLoggedInUser()

    def copyPageVars(clazz, sourcePage, destPage):
        # Copy the page variables from one ypage to another.
        # This is used in templates, where the template page is
        # running as its own ypage instance...
        # (the template page is destPage)
        destPage.Request = sourcePage.Request
        destPage.RequestCtx = sourcePage.RequestCtx
        destPage.ApplicationCtx = sourcePage.ApplicationCtx
        destPage.WebApp = sourcePage.WebApp
        destPage.URLprefix = sourcePage.URLprefix
        destPage.Assetprefix = sourcePage.Assetprefix
        destPage.write=sourcePage.write
        destPage.out=sourcePage.out
        if hasattr(sourcePage,'SessionCtx'): destPage.SessionCtx = sourcePage.SessionCtx
        if hasattr(sourcePage,'User'): destPage.User = sourcePage.User
    copyPageVars=classmethod(copyPageVars)



class Ypage(Snakelet):

    class PageAbortError(Exception):
        def __unicode__(self):
            return unicode(self.args[0])
        def __str__(self):
            return unicode(self.args[0]).encode("unicode-escape")
    class PageSendErrorError(Exception):
        def __init__(self, error, msg=None):
            self.error=error
            self.msg=msg
    class PageRedirectURL(Exception):
        def __init__(self, url):
            self.url=url
    class PageHTTPRedirectURL(Exception):
        def __init__(self, url):
            self.url=url

    def __init__(self, pageName, webappref, pageArgs=None):
        Snakelet.__init__(self, pageName, webappref)
        self.PageArgs=pageArgs or {}    # used for template page arguments.

    def getDescription(self):
        return "Ypage snakelet"
    def getPageEncoding(self):
        return None
    def getPageContentTypeAndDisposition(self):
        return self.getWebApp().defaultContentType,None     # will be overridden in the compiled page if different.
    def templateArgs(self, request):
        return {}           # this pagemethod can be redefined in the ypage
    def createOutput(self, out,_request,_response):
        self.out=out
        self.__request = weakref.ref(_request)
        self.__response = weakref.ref(_response)

        # determine write method to use. Watch out: introduces reference cycle
        # that must be cleared up when we're done!
        if self.getPageEncoding():
            self.write=self._writeUnicode
        else:
            self.write=self._writeString

        try:
            try:
                self.WebApp.addPageHeaders(self, _response)
                if self._ypage_template:
                    # It is a templated page. Load & call the template instead.
                    # (we load it every time instead of caching it here, because you
                    #  want to see changes in the template page work on a page refresh)
                    fulltplpath=self.WebApp.getFullPath(self._ypage_template)
                    tplargs=self.templateArgs(_request)
                    tplargs.update(self._ypage_templateargs or {} )
                    tplpage=self.WebApp.pageEngine.loadPage(fulltplpath,self._ypage_template,self.getWebApp(),tplargs)
                    YpageEngine.copyPageVars(self,tplpage)
                    tplpage.__request=self.__request
                    tplpage.__response=self.__response
                    tplpage.create(out, _request, _response, templatedPage=self)
                else:
                    # Not a templated page; call the method in the actual compiled Ypage source.
                    self.create(out,_request,_response)
            except Ypage.PageAbortError,pax:
                self.out.write("<hr><strong>Page aborted<p>"+unicode(pax)+"</strong>")
            except Ypage.PageSendErrorError,pex:
                _response.sendError(pex.error, pex.msg)
                self.out.truncate(0)
                return
            except Ypage.PageHTTPRedirectURL, prx:
                self.out.truncate(0)
                _response.HTTPredirect(prx.url)
                return
            except Ypage.PageRedirectURL, prx:
                self.out.truncate(0)
                self.redirect(prx.url, _request, _response)
                return
            except Exception,x:
                # oops something went wrong, let the webapp print the traceback.
                self.WebApp.reportSnakeletException(self,x, None, self.out, _request, _response, self.getErrorPage())

        finally:
            sys.exc_clear()
            del self.write          # break ref. cycle to self

        self.out.flush()

    def _writeUnicode(self, strng): # support for "self.write(...)" in page
        self.out.write(unicode(strng))
    def _writeString(self, strng):      # support for "self.write(...)" in page
        self.out.write(str(strng))

    def abort(self,message=''):
        raise Ypage.PageAbortError(message)

    def Ycall(self, URL):
        self.include(URL, self.__request(), self.__response())
    def Yredirect(self, URL):
        raise Ypage.PageRedirectURL(URL)
    def Yhttpredirect(self, URL):
        raise Ypage.PageHTTPRedirectURL(URL)
    def copyPageVars(self, source, dest):
        YpageEngine.copyPageVars(source,dest)   # call the static (class)method

    # some methods that we expose from the response object:
    def sendError(self, error, msg=None):
        raise Ypage.PageSendErrorError(error,msg)
    def getCookies(self):
        return self.__response().getCookies()
    def setCookie(self, *args,**kwargs):
        return self.__response().setCookie(*args,**kwargs)
    def delCookie(self, *args,**kwargs):
        return self.__response().delCookie(*args,**kwargs)
    def guessMimeType(self, filename):
        return self.__response().guessMimeType(filename)
    def setHeader(self, header, value):
        self.__response().setHeader(header,value)
    def setContentType(self, contenttype):
        self.__response().setContentType(contenttype)
    def getHeader(self, header):
        return self.__response().getHeader(header)

