#!/usr/bin/env python
# encoding: utf-8
"""
Referrers.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import urllib

class ReferrersWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','referrers')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    buffer = [u'<table class="compact"><tr><th>%s (%s)</th><th>%s (%s)</th></tr><tbody>' % (self.i18n['Page'],self.i18n['Hits'],self.i18n['Referrers'],self.i18n['Hits'])]
    data = self.ac.referrers.getData()
    pages = data.keys()
    # sort pages by decreasing timestamp of last hit
    pages.sort(lambda b, a: cmp(data[a]['mtime'], data[b]['mtime']))
    for page in pages:
      page = urllib.unquote(page)
      try:
        row = [u'<tr><td><a href="%s" title="%s">%s <small>(%d)</small></a></td><td class="referring_urls">' % (self.ac.base + page, self.i18n['visited_ago_format'] % timeSince(self.i18n,data[page]['mtime']),self.ac.indexer.pageinfo[page]['title'],self.ac.indexer.pageinfo[page]['x-hit-count'])]
        referrers = data[page]['referrers'].keys()
        referrers.sort(lambda b, a: cmp(data[page]['referrers'][a]['mtime'], data[page]['referrers'][b]['mtime']))
        for referrer in referrers:
          row.append(u'<a target="_new" href="%s" title="%s">%s</a>&nbsp;<small>(%d)</small><br/>' % (referrer, self.i18n['visited_ago_format'] % timeSince(self.i18n, data[page]['referrers'][referrer]['mtime']), shrink(referrer,50), data[page]['referrers'][referrer]['count']))
        buffer.append(u''.join(row)[:-5]) # append current partial row trimming trailing <br/>
        buffer.append(u'</td></tr>')
      except:
        print "INFO: Error processing referrers for %s" % page
        pass
    buffer.append(u'</table>')
    tag.replaceWith(u''.join(buffer))
