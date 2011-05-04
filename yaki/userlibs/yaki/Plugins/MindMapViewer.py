#!/usr/bin/env python
# encoding: utf-8
"""
MindMapViewer.py

Flash-based mindmap viewer

Created by Rui Carmo on 2007-01-16.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
from yaki.Utils import *
from BeautifulSoup import *
import re, urlparse


template = """
<div id="mindmap%d"><a href="http://www.macromedia.com/go/getflashplayer">Get the Flash Player</a> to see this mindmap.</div>
<script type="text/javascript">
  $('#mindmap%d').flash({
    src: '/flash/mmplayer.swf',
    width: %s,
    height: %s,
    version: 6,
  	flashvars: {
  	  initLoadFile: '%s',
  	  openUrl: '_blank',
  	  startCollapsedToLevel: '5',
  	  defaultWordWrap: '400',
  	  defaultToolTipWordWrap: '200',
  	  scaleTooltips: 'false',
  	  buttonsPos: 'bottom',
  	  max_alpha_buttons: '255'
  	}
  });
</script>
"""

class MindMapViewerWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.ac = webapp.getContext()
    registry.register('markup',self, 'plugin','mindmap')

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
      tag.replaceWith(template % (serial,serial,width, height, src))
      # No further processing is required
      return False
    return True
     
    
    