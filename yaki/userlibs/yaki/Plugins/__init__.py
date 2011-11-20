#!/usr/bin/env python
# encoding: utf-8
"""
__init__.py

Plugin registration and invocation

Created by Rui Carmo on 2006-11-12.
Published under the MIT license.
"""

import os, re
import logging
from yaki.Utils import *

log=logging.getLogger("Snakelets.logger")

class PluginRegistry:
  plugins = {'markup': {}}
  serial = 0
  
  def __init__(self, webapp):
    """Load wiki plugins. Assumptions are that they are inside the plugins directory 
       under the yaki tree, in userlibs, so we can use standard import..."""
    log.info("Loading Wiki plugins...")
    self.ac = webapp.getContext()
    # Get plugin directory
    plugindir = yaki.Plugins.__path__[0]
    for f in locate('*.py', plugindir):
      relpath = f.replace(plugindir + '/','')
      (modname,ext) = rsplit(relpath, '.', 1)
      modname = '.'.join(modname.split('/'))
      try:
        _module = __import__(modname,globals(), locals(), [''])
        for x in dir(_module):
          if 'WikiPlugin' in x:
            _class = getattr(_module, x)
            _class(self,webapp) # plugins will register themselves
      except ImportError:
        pass
    
  def register(self, category, instance, tag, name):
    log.info("%s: Plugin %s registered in category %s for tag %s" % (self.ac.name, name, category, tag))
    if tag not in self.plugins[category].keys():
      self.plugins[category][tag] = {}
    self.plugins[category][tag][name.lower()] = instance
  
  def runForAllTags(self, pagename, soup, request=None, response=None, indexing=False):
    """Runs all markup plugins that process specific tags (except the plugin one)"""
    for tagname in self.plugins['markup'].keys():
      if tagname != 'plugin':
        order = self.plugins['markup'][tagname].keys()
        order.sort()
        for i in order:
          plugin = self.plugins['markup'][tagname][i]
          for tag in soup(tagname):
            result = plugin.run(self.serial, tag, tagname, pagename, soup, request, response)
            self.serial = self.serial + 1
            if result == True:
              continue

  def run(self, tag, tagname, pagename = None, soup = None, request=None, response=None, indexing=False):
    if tagname == 'plugin':
      try:
        name = tag['name'].lower() # get the attribute
      except KeyError:
        return
      if name in self.plugins['markup']['plugin']:
        plugin = self.plugins['markup']['plugin'][name]
        if not indexing:
          result = plugin.run(self.serial, tag, tagname, pagename, soup, request, response)
          self.serial = self.serial + 1
        else:
          tag.replaceWith('')
        # ignore the result for plugin tags
    elif tagname in self.plugins['markup']:
      for i in self.plugins['markup'][tagname]:
        plugin = self.plugins['markup'][tagname][i]
        result = plugin.run(self.serial, tag, tagname, pagename, soup, request, response)
        self.serial = self.serial + 1
        # if plugin returns False, then the tag does not need to be processed any further
        if result == False:
          return

class WikiPlugin:
  """
  Base class for all Wiki plugins
  """

  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin', 'base')
  
  def run(self, serial, tag, tagname, pagename, soup, request = None, response = None, indexing = False):
    pass
  
  
