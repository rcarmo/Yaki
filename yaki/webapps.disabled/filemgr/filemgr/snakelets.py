import os

from snakeserver.snakelet import Snakelet

class DownloadFile(Snakelet):

    def requiresSession(self):
        return self.SESSION_LOGIN_REQUIRED

    def getDescription(self):
        return "serves files"

    def serve(self, request, response):
        response.setEncoding(None) # no encoding
        user=request.getSession().getLoggedInUser()
        selected_idx=int(request.getParameter("i"))
        selected = request.getSessionContext().filelist[selected_idx]
        ctype=response.guessMimeType(selected)
        filename = os.path.normpath(user.directory+request.getSessionContext().currentpath+selected)
        if not filename.startswith(user.directory):
            response.sendError(403) # denied
        try:
            if not os.path.isfile(filename):
                raise IOError("is not a file")
            stats = os.stat(filename)
        except EnvironmentError,x:
            response.sendError(404, str(x))
            return
        else:
            # set content-disposition so that the file is always downloaded instead of opened in the browser
            response.setContentDisposition("'attachment; filename=\"%s\"" % os.path.split(filename)[1])
            self.getWebApp().serveStaticFile(filename, response, True)   # use response headers (nocache, contentdisposition etc)
