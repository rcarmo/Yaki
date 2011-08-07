#!/usr/bin/env python
# encoding: utf-8
"""
Loupe.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
from yaki.Utils import *
from BeautifulSoup import *
import re, urlparse

template = """
<div id="loupe%(serial)d" style="width:%(width)spx; height:%(height)spx; background:url(%(small)s) no-repeat; border:1px solid gray; margin-right: 1em; margin-bottom: 0.25em;">
<img id="loupeimg%(serial)d" onLoad="initLoupe(this.id,true);" src="%(large)s" style="cursor:wait; margin:0px; padding:0px; border: none;" width="%(width)s" height="%(height)s" border="0" />
</div>
"""

class LoupeWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.ac = webapp.getContext()
    registry.register('markup', self, 'plugin','loupe')

  def run(self, serial, tag, tagname, pagename, soup, request, response):  
    params = {'serial':serial}
    try:
      params['large'] = tag['src']
      params['small'] = tag['alt']
      params['width'] = tag['width']
      params['height'] = tag['height']
    except KeyError:
      return True
    
    for image in ['large','small']:
      # Try to handle the uri as a schema/path pair
      (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(params[image])

      if schema.lower() in ATTACHMENT_SCHEMAS or self.ac.store.isAttachment(pagename, path):
        params[image] = self.ac.media + pagename + "/" + path
      else:
        return True

    tag.replaceWith(template % params)
    # No further processing is required
    return False
     
    
    
