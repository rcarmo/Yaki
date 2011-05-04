import cgi, urllib
from snakeserver.snakelet import Snakelet

import logging
log=logging.getLogger("Snakelets.logger")

# the Server's management interface!
# fully coded as a Snakelet... 

class Manager(Snakelet):

    # no special init method

    def getDescription(self):
        return "Server and WebApp management interface"

    def requiresSession(self):
        return self.SESSION_LOGIN_REQUIRED      # requires user to be logged in

    def serve(self, request, response):
        f=request.getForm()
        if f.has_key('action'):
            action=f['action']
            if action=='shutdown':
                out = response.getOutput()
                print >>out,'<html><head><title>Shutdown</title><link rel="stylesheet" type="text/css" href="manage.css"></head><body><h2>Server shutdown</h2>'
                print >>out, "<p>Shutting down.</p><p>Okay, now do <a href=\"http://www.google.com/search?q=something+else\">something else</a>.</p></body></html>"
                self.getWebApp().server.shutdown()
                return
            elif action in ("disable", "enable", "reload", "destroy", "clearcache"):
                name=f.get('name') or ""
                vhost=f['vhost']
                urlname=urllib.quote_plus(name)
                if action=="disable":
                    self.getWebApp().server.enableWebApp(vhost, name,False)
                    request.getContext().actionmsg="disabled the webapp"
                    if not self.getWebApp().isEnabled():
                        # heh, the management app itself has been disabled. Go to an exit page.
                        out = response.getOutput()
                        print >>out,'<html><head><title>Disabled</title><link rel="stylesheet" type="text/css" href="manage.css"></head><body><h2>Management console disabled</h2>'
                        print >>out, "<p>The management console is no longer running.</p><p>Well, go do <a href=\"http://www.google.com/search?q=something+else\">something else</a>.</p></body></html>"
                        return
                elif action=="enable":
                    self.getWebApp().server.enableWebApp(vhost, name,True)
                    request.getContext().actionmsg="enabled the webapp"
                elif action=="reload":
                    realname=f.get('realname')
                    if self.getWebApp().server.reloadWebApp(vhost, name, realname):
                        request.getContext().actionmsg="reloaded and enabled the webapp"
                    else:
                        request.getContext().actionmsg="webapp NOT reloaded, is it deployed multiple times?"
                    if not urlname:
                        self.redirect("serverinfo.y",request,response)
                        return
                elif action=="clearcache":
                    self.getWebApp().server.clearWebAppCache(vhost, name)
                    request.getContext().actionmsg="page cache has been cleared"
                elif action=="destroy":
                    selfWebApp=self.getWebApp()
                    destroyedSelf = (vhost==selfWebApp.getVirtualHost()[0]) and (name==selfWebApp.getURLprefix())
                    log.info( "UNLOADING WEBAPP '%s' [%s]" % (name, vhost) )
                    selfWebApp.server.unloadWebApp(vhost, name)
                    if destroyedSelf:
                        # heh, the management app itself has been disabled. Go to an exit page.
                        out = response.getOutput()
                        print >>out,'<html><head><title>Destroyed</title><link rel="stylesheet" type="text/css" href="manage.css"></head><body><h2>Management console destroyed</h2>'
                        print >>out, "<p>The management console has been destroyed.</p><p>Well, go do <a href=\"http://www.google.com/search?q=something+else\">something else</a>.</p></body></html>"
                        return
                    self.redirect(selfWebApp.getURLprefix()+"serverinfo.y",request,response)
                    return
                # ..and back to the webapp page.
                self.redirect("webappinfo.y?name="+urlname, request, response)
            elif action=='killsession':
                webapp=f['webapp']
                vhost=f['vhost']
                urlname=urllib.quote_plus(webapp)
                sessionid=f['id']
                activesessions = self.getWebApp().server.allWebApps[(vhost,webapp)].sessions
                if sessionid=='all':
                    for (sessionID,session) in activesessions.items() [:] :
                        log.info("KILLING SESSION "+sessionID)
                        session.destroy(external=True)
                        del activesessions[sessionID]
                else:
                    log.info("KILLING SESSION "+sessionid)
                    activesessions[sessionid].destroy(external=True)
                    del activesessions[sessionid]
                # ..and back to the webapp session page.
                self.redirect("sessions.y?webapp="+urlname, request, response)
                    
            else:
                response.sendError(501,"invalid command")
        else:
            # no action specified, go to the start page.
            self.redirect(self.getWebApp().getURLprefix()+"serverinfo.y",request,response)
