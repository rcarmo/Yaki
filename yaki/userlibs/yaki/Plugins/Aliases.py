#!/usr/bin/env python
# encoding: utf-8
"""
Aliases.py

Created by Rui Carmo on 2009-10-04.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
import urlparse, re, time
from BeautifulSoup import *

metaPage = 'meta/Aliases'

class AliasesWikiPlugin(yaki.Plugins.WikiPlugin):
  """Handles a list of hard-coded aliases for Wiki nodes"""
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'a','aliases')
    self.ac = webapp.getContext()
    self.load()
    
  def load(self):
    # load Alias map
    try:
      page = self.ac.store.getRevision(metaPage)
    except:
      print "WARNING: no %s definitions" % metaPage
      return
    self.aliases = {}
    # prepare to parse only <pre> tags in it (so that we can have multiple maps organized by sections)
    plaintext = SoupStrainer('pre')
    map = ''.join([text.string for text in BeautifulSoup(page.render(), parseOnlyThese=plaintext)])
    # now that we have the full map, let's build the alias hash
    lines = map.split('\n')
    for line in lines:
      try:
        (link, alias) = line.strip().split(' ',1)
        self.aliases[link] = alias
        self.aliases[link.replace('_',' ')] = alias
      except ValueError: # skip lines with more than two fields
        pass
    self.mtime = time.time()
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    try:
      if (self.mtime < self.ac.store.mtime(metaPage)):
        self.load()
    except:
      return True
    try:
      url = tag['href']
    except KeyError:
      return True
    while True: # expand multiple aliases if required
      stack = [] # avoid loops
      try:
        alias = self.aliases[tag['href']]
        if alias not in stack:
          stack.append(alias)
          tag['href'] = alias
        else: # avoid loops
          return True
      except:
        return True
    # this tag may need to be re-processed to expand interwiki links and whatnot
    return True
