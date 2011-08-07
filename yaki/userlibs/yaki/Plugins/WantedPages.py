#!/usr/bin/env python
# encoding: utf-8
"""
WantedPages.py

Created by Rui Carmo on 2009-09-30.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import urllib

class WantedPagesWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','wantedpages')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    if not self.ac.indexer.done:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['indexing_message'])
      return False
    
    buffer = [u'<table class="compact"><thead><tr><th>%s</th><th>%s</th></tr></thead><tbody>' % (self.i18n['Missing References'],self.i18n['Page'])]
    
    pageinfo = self.ac.indexer.pageinfo
    pages = self.ac.indexer.wantedlinks.keys()
    wantedlinks = {}
    for page in pages:
      links = self.ac.indexer.wantedlinks[page]
      for link in links:
        try:
          wantedlinks[link].append(page)
        except:
          wantedlinks[link] = [page]
    data = []
    for link in wantedlinks.keys():
      items = wantedlinks[link]
      items.sort(lambda b,a: cmp(a,b))
      data.append([link, len(items), items])
    data.sort(lambda b, a: cmp(a[1],b[1]))

    for pair in data:
      item = pair[0]
      mentions = pair[2]
      try:
        row = [u'<tr><td><a href="%s" title="%s">%s</a></td><td class="referring_urls">' % (self.ac.base + item, self.i18n['updated_ago_format'] % timeSince(self.i18n, pageinfo[item]['last-modified']), item)]
      except:
        row = [u'<tr><td><a href="%s">%s</a></td><td class="referring_urls">' % (self.ac.base + item, item)]
      for mention in mentions:
        row.append(u'<a href="%s">%s</a><br/>' % (self.ac.base + mention, mention))
      buffer.append(u''.join(row)[:-5]) # append current partial row trimming trailing <br/>
      buffer.append(u'</td></tr>')
    buffer.append(u'</tbody></table>')
    tag.replaceWith(u''.join(buffer))
