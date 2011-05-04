#!/usr/bin/env python
# encoding: utf-8
"""
RecentChanges.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import re, yaki.Engine, yaki.Store, yaki.Locale
from yaki.Utils import *
from BeautifulSoup import *

class RecentChangesWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','RecentChanges')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]

  def run(self, serial, tag, tagname, pagename, soup, request, response):    
    recent = self.ac.indexer.recent[:50]
    buffer = [u'<table class="compact"><tr><th>%s</th><th>%s</th><th>%s</th></tr><tbody>' % (self.i18n['Page'],self.i18n['Created'],self.i18n['Modified'])]
    for name in recent:
      try:
        headers = self.ac.indexer.pageinfo[name]
      except:
        page = self.ac.store.getRevision(name)
        headers = page.headers  
      headers['name'] = self.ac.base + name
      headers['plaintime'] = plainTime(self.i18n, headers['date'])
      headers['timesince'] = self.i18n['updated_ago_format'] % timeSince(self.i18n,headers['last-modified'])
      buffer.append(u"""<tr><td><a href="%(name)s">%(title)s</a></td><td>%(plaintime)s</td><td>%(timesince)s</td></tr>""" % headers)
    buffer.append(u"</tbody></table>")
    tag.replaceWith(u''.join(buffer))
