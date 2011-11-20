#!/usr/bin/env python
# encoding: utf-8
"""
SimpleGallery.py

Created by Rui Carmo on 2008-04-21.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from yaki.Utils import *
from BeautifulSoup import *
import re, urlparse

template = """
<script type="text/javascript">
$(document).ready(function(){
	$('#%(id)s').gallery();
	$('a[rel=%(id)s]').fancybox({'centerOnScroll':true, 'titlePosition':'over', 'opacity': true, 'overlayShow': true, 'transitionIn': 'elastic', 'transitionOut': 'none'});
});
</script>
"""

class SimpleGalleryWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.webapp = webapp
    registry.register('markup', self, 'plugin','simplegallery')
    self.ac = webapp.getContext() 
    self.i18n = yaki.Locale.i18n[self.ac.locale]


  def run(self, serial, tag, tagname, pagename, soup, request, response):  
    params = {'serial':serial,'align':'horizontal'}
    try:
      params['id'] = tag['id']
    except KeyError:
      return True
      
    try:
      params['align'] = tag['align']
    except KeyError:
      pass
    tag.replaceWith(template % params)
    # No further processing is required
    return False
     
    
    
