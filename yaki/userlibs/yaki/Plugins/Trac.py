#!/usr/bin/env python
# encoding: utf-8
"""
Trac.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import re, yaki.Engine, yaki.Store
from yaki.Utils import *
from BeautifulSoup import *

class TracWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','Trac')
    self.webapp = webapp
    self.context = webapp.getContext()

  def run(self, serial, tag, tagname, pagename, soup, request, response):
    c = self.context
    # filter for the trac namespace
    mask = re.compile('^trac/*')
    proj = re.compile('^trac/(?P<project>.+)/(?P<ref>*)')
    # find trac entries
    paths = [path for path in c.indexer.recent if mask.match(path)]
    projects = {}
    for i in paths:
      m = proj.match(i)
      if m is not None:
        project = m.group('project')
        ref = m.group('ref')
        if project not in projects.keys():
          projects[project] = {}
        else:
          projects[project][ref] = (c.indexer.pageinfo[i])
    
    for p in projects.keys():
      for r in projects[p].keys():
        pass
    tag.replaceWith('')
