#!/usr/bin/env python
# encoding: utf-8
"""
SeeAlso.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
from BeautifulSoup import *

try:
  import cPickle as pickle
except ImportError:
  import pickle # fall back on Python version

class SeeAlsoWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','seealso')
    self.context = webapp.getContext()
    self.cache = self.context.cache
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    # fetch the cached backlinks for this page
    try:
      backlinks = pickle.loads(self.cache['backlinks:' + pagename])
    # fail silently if no backlinks are found
    except:
      return True
    buffer = []
    for href in backlinks:
      buffer.append('<a href="%s">%s</a> ' % (href,backlinks[href]))
    tag.replaceWith(''.join(buffer))

