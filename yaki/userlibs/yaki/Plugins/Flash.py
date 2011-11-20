#!/usr/bin/env python
# encoding: utf-8
"""
Flash.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
from yaki.Utils import *
from BeautifulSoup import *
import re, urlparse

template = """
<div id="flashmovie%d"><a href="http://www.macromedia.com/go/getflashplayer">Get the Flash Player</a> to see this movie.</div>
<script type="text/javascript">
  $('#flashmovie%d').flash({
    src: '%s',
    width: %s,
    height: %s,
    version: 7
  });
</script>
"""

class FlashMovieWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.ac = webapp.getContext()
    registry.register('markup',self, 'plugin','flash')

  def run(self, serial, tag, tagname, pagename, soup, request, response):  
    try:
      src = tag['src']
      width = tag['width']
      height = tag['height']
    except KeyError:
      return True

    # Try to handle the uri as a schema/path pair
    (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(src)

    if schema.lower() in ATTACHMENT_SCHEMAS or self.ac.store.isAttachment(pagename, path):
      src = self.ac.media + pagename + "/" + path
      tag.replaceWith(template % (serial,serial,src,width,height))
      # No further processing is required
      return False
    return True
     
    
    
