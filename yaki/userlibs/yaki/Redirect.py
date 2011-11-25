from snakeserver.snakelet import Snakelet

class Redirect(Snakelet):
  """
  Redirect to wiki home page (start).
  TODO: achieve this in a more elegant way?
  """
  def getDescription(self):
    return "Redirector"

  def allowCaching(self):
    return True

  def requiresSession(self):
    return self.SESSION_DONTCREATE

  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    a = request.getWebApp()
    ac = a.getContext()
    response.HTTPredirect("%s/start" % ac.siteinfo['siteroot'])
    return