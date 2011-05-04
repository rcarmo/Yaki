 #!/usr/bin/env python
# encoding: utf-8
"""
Quicklook.py

Created by Rui Carmo on 2007-09-21.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from yaki.Utils import *
from BeautifulSoup import *
import re, urlparse

#<script>$.preloadImages("%(large)s");</script>
template = """
<div class="quicklook_holder"%(align)s><a title="%(title)s" href="%(large)s" class="quicklook"><img alt="%(alt)s" src="%(small)s" class="thumb"></a></div>
"""

class QuickLookWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.webapp = webapp
    registry.register('markup', self, 'plugin','quicklook')
    self.ac = webapp.getContext() 
    self.i18n = yaki.Locale.i18n[self.ac.locale]


  def run(self, serial, tag, tagname, pagename, soup, request, response):  
    params = {'serial':serial,'align':''}
    try:
      params['large'] = tag['alt']
      params['small'] = tag['src']
    except KeyError:
      print "Error in tag parameters for %s in %s" % (str(tag), pagename)
      return True
      
    try:
      params['align'] = tag['align']
    except KeyError:
      pass
    
    try:
      params['title'] = tag['title']
    except KeyError:
      params['title'] = ''
      pass
    
    if params['align'] != '':
      params['align'] = ' align="%s"' % params['align']
    
    for image in ['large','small']:
      (schema,host,path,parameters,query,fragment) = urlparse.urlparse(params[image])
      if self.ac.store.isAttachment(pagename, params[image]):
        c = self.webapp.getContext()
        params[image] = c.media + pagename + "/" + params[image]
      elif schema in ['http','https']:
        pass # allow us to link to remote images if we really want to
      else:
        print "Missing attachment %s (%s) in %s" % (image, params[image], pagename)
        return True

    params['alt'] = self.i18n['quicklook_click_to_zoom']
    tag.replaceWith(template % params)
    # No further processing is required
    return False
     
    
    
