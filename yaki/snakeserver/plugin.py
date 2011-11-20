#############################################################################
#
#	$Id: plugin.py,v 1.26 2006/04/22 14:03:25 irmen Exp $
#	Server Plugin Management
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import logging
import os

log=logging.getLogger("Snakelets.logger")

# Plugin sequence 0 to 1000
SEQUENCE_FIRST  = 1000
SEQUENCE_EARLY  = 800
SEQUENCE_NORMAL = 500
SEQUENCE_LATE   = 200
SEQUENCE_LAST   = 0


# The abstract Plugin class all other plugins must inherit from.
# (you cannot use this as a base class for your own plugins, you
#  must choose one of the specific plugin classes below.)
class PluginBase(object):
    def __init__(self, seq=SEQUENCE_NORMAL, name=None):
        self.sequence=seq
        self.name=name
    def __cmp__(self, other):
        return other.sequence-self.sequence
    def __str__(self):
        return "<plugin '%s' seq %d>" % (self.name, self.sequence)
    def __repr__(self):
        return self.__str__()
    def plug_init(self,server):
        pass


# PLUGIN CLASS that you can inherit from, to handle server-oriented events:
class ServerPlugin(PluginBase):
    def __init__(self, seq=SEQUENCE_NORMAL, name=None):
        PluginBase.__init__(self, seq, name)
    def plug_serverStart(self, server):
        pass
    def plug_serverStop(self, server):
        pass
    def plug_sessionCreated(self, webapp, session, request):
        pass
    def plug_sessionDestroyed(self, webapp, session, request):
        pass

# PLUGIN CLASS that you can inherit from, to make your own page processor
class PageProcessorPlugin(PluginBase):
    def __init__(self, seq=SEQUENCE_NORMAL, name=None):
        PluginBase.__init__(self, seq, name)
    def plug_getPageProcessor(self, webapp, handler, url, pathpart, query):
        # if you have your own page processor, return it, otherwise return None
        return None


# PLUGIN CLASS that you can inherit from, to handle request-oriented events:
#   XXX  will only be called for dynamic pages.... Fix this!? Or add another plugin?
#        (likely that a lower-level plugin is needed; static pages don't have a request/response object)
class RequestPlugin(PluginBase):
    def __init__(self, seq=SEQUENCE_NORMAL, name=None):
        PluginBase.__init__(self, seq, name)
    def plug_requestExecute(self, webapp, snakelet, request, response):
        # If you want to let the regular page run after your plugin code,
        # just return False or None (this is usually the case).
        # But if you hijack the output (and not let the regular page run!),
        # you must return the new page output (string/unicode).
        return False
    def plug_requestFinished(self, webapp, snakelet, request, response, outputarray=[None]):
        # Note that the output object is passes inside an array, so that you can
        # change this array (replace the output object), and pass it on to the next plugin.
        # (the content-length header will be correct even if you change the output size)
        # You have to return True to let the page processing stop (no more plugins called),
        # and return False to let processing continue with the next plugin.
        return False


# PLUGIN CLASS that you can inherit from, to customize the server's 404/500/etc error pages
# This is a low-level error handler because it doesn't know about the Snakelet Request object.
class ErrorpagePlugin(PluginBase):
    def __init__(self, seq=SEQUENCE_NORMAL, name=None):
        PluginBase.__init__(self, seq, name)
    def plug_serverErrorpage(self, path, code, message, explainTxt, outputStream):
        # return True if the page has been handled, False for default page.
        return False
        
        
class SortedPluginDict(dict):
    def __init__(self, *args):
        self.sortedlist=[]
        dict.__init__(self, *args)
    def __setitem__(self, key, value):
        dict.__setitem__(self, key,value)
        self.sortedlist=self.values()
        self.sortedlist.sort()   
    
PLUGINDIR = "plugins"

class PluginRegistry(object):
    def __init__(self):
        self.serverPlugins=SortedPluginDict()
        self.requestPlugins=SortedPluginDict()
        self.errorpagePlugins=SortedPluginDict()
        self.pageProcessorPlugins=SortedPluginDict()
        self.webapps={}
    def load(self, server):
        log.info("Loading plugins...")
        self.server=server
        path=os.path.abspath(__file__)
        path=os.path.join(os.path.split(path)[0], PLUGINDIR)
        for fn in os.listdir(path):
            fullfn = os.path.join(path, fn)
            if os.path.isdir(fullfn):
                if fn=="CVS" or fn==".svn":
                    continue
                log.info("Loading plugin module: %s", fn)
                try:
                    module = __import__("snakeserver.plugins.%s" % fn, locals())
                    module = getattr(module.plugins,fn)
                    enabled=getattr(module,"ENABLED", True)
                    if enabled and module.PLUGINS:
                        for pluginname in module.PLUGINS:
                            log.info("Loading plugin: "+pluginname)
                            clazz=getattr(module, pluginname)
                            plugin=clazz()  # call __init__
                            othername=getattr(plugin,"PLUGIN_NAME", getattr(plugin,"name"))
                            if othername:
                                pluginname=othername
                            plugin.name=pluginname
                            plugin.sequence=getattr(plugin,"PLUGIN_SEQ", getattr(plugin,"sequence"))
                            plugin.plug_init(self.server)
                            self.__getPluginCategory(clazz) [pluginname] = plugin
                            self.webapps[pluginname]=None   # not belonging to a specific webapp
                except Exception,x:
                    log.error("Problem initializing plugin module %s: %s", fn, x)
                    raise
        
    def addPlugin(self, webapp, plugin):
        if not isinstance(plugin, PluginBase):
            raise TypeError("plugin class doesn't inherit from PluginBase")
        category = self.__getPluginCategory(plugin.__class__)
        plugin.name=getattr(plugin,"PLUGIN_NAME", getattr(plugin,"name"))
        plugin.name=name=webapp.getName()[0]+"/"+(plugin.name or plugin.__class__.__name__)
        plugin.sequence=getattr(plugin,"PLUGIN_SEQ", getattr(plugin,"sequence"))
        plugin.plug_init(webapp.server)
        if name in self.webapps:
            raise ValueError("plugin already registered: "+name)
        category[name] = plugin
        self.webapps[name]=webapp.getName()

    def _addServerPlugin(self, server, plugin):
        if not isinstance(plugin, PluginBase):
            raise TypeError("plugin class doesn't inherit from PluginBase")
        category = self.__getPluginCategory(plugin.__class__)
        plugin.name=getattr(plugin,"PLUGIN_NAME", getattr(plugin,"name"))
        plugin.name=name= plugin.name or plugin.__class__.__name__
        plugin.sequence=getattr(plugin,"PLUGIN_SEQ", getattr(plugin,"sequence"))
        plugin.plug_init(server)
        if name in self.webapps:
            raise ValueError("plugin already registered: "+name)
        category[name] = plugin
        self.webapps[name]=None # not belonging to a specific webapp

    def getPlugin(self, name):
        if self.serverPlugins.has_key(name):
            return self.serverPlugins[name]
        elif self.pageProcessorPlugins.has_key(name):
            return self.pageProcessorPlugins[name]
        elif self.requestPlugins.has_key(name):
            return self.requestPlugins[name]
        elif self.errorpagePlugins.has_key(name):
            return self.errorpagePlugins[name]
        else:
            raise KeyError("plugin not found: "+name)
    def getPluginNames(self):
        return self.serverPlugins.keys() + self.pageProcessorPlugins.keys() + self.requestPlugins.keys() + self.errorpagePlugins.keys()

    def __getPluginCategory(self, pluginclass):
        if issubclass(pluginclass, ServerPlugin):
            return self.serverPlugins
        elif issubclass(pluginclass, PageProcessorPlugin):
            return self.pageProcessorPlugins
        elif issubclass(pluginclass, RequestPlugin):
            return self.requestPlugins
        elif issubclass(pluginclass, ErrorpagePlugin):
            return self.errorpagePlugins          
        else:
            raise TypeError("Plugin is not of a recognized class: "+str(pluginclass))
        
    def __doall(self, plugins, pluginMethod, *args):
        # perform a specific method on the given plugins. (no returnvalue)
        for plugin in plugins:
            method=getattr(plugin,pluginMethod)
            try:
                method(*args)
            except Exception,x:
                log.warn("error while executing %s: Plugin %s error: %s,%s", pluginMethod,plugin.name,x.__class__.__name__,x )

    def __doall_returnval(self, plugins, pluginMethod, *args):
        # perform a specific method on the given plugins.
        # stop as soon as a method returns something (not None) and return that value
        for plugin in plugins:
            method=getattr(plugin,pluginMethod)
            try:
                result = method(*args)
                if result not in (False, None):
                    return result
            except Exception,x:
                log.warn("error while executing %s: Plugin %s error: %s,%s", pluginMethod,plugin.name,x.__class__.__name__,x )
        return None

    def __doall_WA_returnval(self, plugins, pluginMethod, webapp, *args):
        # perform a specific method on the given plugins, but only if the webapp is the same (or None)
        # stop as soon as a method returns something (not None) and return that value
        webappname=webapp.getName()
        for plugin in plugins:
            if self.webapps[plugin.name] in (None, webappname):
                method=getattr(plugin,pluginMethod)
                try:
                    result = method(webapp, *args)
                    if result not in (False, None):
                        return result
                except Exception,x:
                    log.warn("error while executing %s: Plugin %s error: %s,%s", pluginMethod,plugin.name,x.__class__.__name__,x )
        return None

    def __doall_WA(self, plugins, pluginMethod, webapp, *args):
        # perform a specific method on the given plugins, but only if the webapp is the same (or None)
        webappname=webapp.getName()
        for plugin in plugins:
            if self.webapps[plugin.name] in (None, webappname):
                method=getattr(plugin,pluginMethod)
                try:
                    method(webapp, *args)
                except Exception,x:
                    log.warn("error while executing %s: Plugin %s error: %s,%s", pluginMethod,plugin.name,x.__class__.__name__,x )


    # SERVERPLUGIN CALLBACKS
    
    def serverStart(self):
        self.__doall(self.serverPlugins.sortedlist,"plug_serverStart", self.server)
    def serverStop(self):
        log.info("Stopping plugins...")
        self.__doall(self.serverPlugins.sortedlist,"plug_serverStop", self.server)
    def sessionCreated(self, webapp, session, request):
        self.__doall_WA(self.serverPlugins.sortedlist,"plug_sessionCreated", webapp, session, request)
    def sessionDestroyed(self, webapp, session, request):
        self.__doall_WA(self.serverPlugins.sortedlist,"plug_sessionDestroyed", webapp, session, request)

    # CUSTOM ERROR PAGE CALLBACK
    def serverErrorpage(self, path, code, message, explain, output):
        return self.__doall_returnval(self.errorpagePlugins.sortedlist,"plug_serverErrorpage", path, code, message, explain, output)
        

    # PAGEPROCESSOR CALLBACKS
    def getPageProcessor(self, webapp, handler, url, pathpart, query):
        return self.__doall_WA_returnval(self.pageProcessorPlugins.sortedlist,"plug_getPageProcessor", webapp, handler, url, pathpart, query)
    def requestExecute(self, webapp, snakelet, request, response):
        return self.__doall_WA_returnval(self.requestPlugins.sortedlist,"plug_requestExecute", webapp, snakelet, request, response)
    def requestFinished(self, webapp, snakelet, request, response, output=None):
        # wrap the output in an array, so that the plugins may modify it (and pass it on to others)
        outarray=[output]
        self.__doall_WA_returnval(self.requestPlugins.sortedlist,"plug_requestFinished", webapp, snakelet, request, response, outarray )
        return outarray[0]



