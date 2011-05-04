#!/usr/bin/env python
# encoding: utf-8
"""
MostPopular.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import urllib

class MostPopularWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','mostpopular')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    src = 'hits'
    try:
      src = tag['src']
    except:
      pass
    if src not in ['time', 'hits']:
      src = 'hits'
      
    buffer = [u'<table class="compact"><tr><th>%s</th><th>%s</th></tr><tbody>' % (self.i18n['Page'],self.i18n['Hits'])]
    data = self.ac.indexer.pageinfo
    # find pages with hit counts
    pages = [x for x in data.keys() if 'x-hit-count' in data[x].keys()]
    if src == 'hits':
      # sort pages by decreasing hit count
      pages.sort(lambda b, a: cmp(data[a]['x-hit-count'], data[b]['x-hit-count']))
      pages = pages[:20]
    elif src == 'time':
      # sort pages by decreasing hit time
      pages.sort(lambda b, a: cmp(data[a]['x-last-hit'], data[b]['x-last-hit']))
      pages = pages[:20]
    else:
      return True
    
    for page in pages:
      page = urllib.unquote(page)
      try:
        row = u'<tr><td><a href="%s" title="%s">%s</td><td align="right">%d</td></tr>' % (self.ac.base + page, self.i18n['visited_ago_format'] % timeSince(self.i18n,data[page]['x-last-hit']),self.ac.indexer.pageinfo[page]['title'],self.ac.indexer.pageinfo[page]['x-hit-count'])
        buffer.append(row)
      except:
        print "INFO: Error processing hit data for %s" % page
        pass
    buffer.append(u'</table>')
    tag.replaceWith(u''.join(buffer))
