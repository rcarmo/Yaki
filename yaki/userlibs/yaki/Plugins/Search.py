#!/usr/bin/env python
# encoding: utf-8
"""
Search.py

Created by Rui Carmo on 2010-04-10.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
from yaki.Utils import *
from BeautifulSoup import *
import re, difflib

import logging
log=logging.getLogger("Snakelets.logger")

class SearchWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.bound = 20
    self.webapp = webapp
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
    registry.register('markup',self, 'plugin','Search')

  def run(self, serial, tag, tagname, pagename, soup, request, response):  
    if 'Mediapartners-Google' in request.getUserAgent():
      return False

    if not self.ac.indexer.done:
      tag.replaceWith(u'<div class="warning">%s</div>' % self.i18n['search_disabled'])    
      return False

    buffer = self.i18n['no_search']
    q = request.getParameter('q', default=None)
    if q == None:
      tag.replaceWith(buffer)
      return False

    q = q.strip() # REMINDER: do not lowercase the string. EVER, because Woosh can do boolean queries.
    try:
      self.ac.notifier.send(self.webapp.getConfigItem('jid'), "Search: %s\n%s -  %s" % (q, request.getRealRemoteAddr(), request.getUserAgent()))
    except Exception, e:
      log.debug("error during notification: %s", e)
      pass
    
    # TODO - add some templating to get rid of this inline HTML
    buffer = []
    log.debug("Search performed on %s" % self.ac.name)
    hits = self.ac.indexer.search(q,limit=20)
    if hits == None or not len(hits):
      buffer.append(u'<p>%s <b>"%s"</b>.</p>' % (self.i18n['no_results'], q))
    else:
      buffer.append(u'<p>%s <b>"%s"</b>:</p>' % (self.i18n['search_results'], q))
      buffer.append(u'<table class="table table-condensed" width="100%%"><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>' % (self.i18n['Page'], self.i18n['Created'], self.i18n['Updated']))
      # transform result into array
      hits = [hit for hit in hits]
      # Sort hits by last-modified date, which is indexed
      hits.sort(lambda x, y: cmp(y['modified'],x['modified']))
      for hit in hits:
        title = hit['title']
        page = hit['name']
        info = self.ac.indexer.pageinfo[page]
        buffer.append(u"""<tr><td><a href="%s">%s</a></td><td rel="%d" align="right">%s</td><td rel="%d" align="right">%s</td></tr>""" % (
          self.ac.base + page, 
          title,
          info['date'],
          self.i18n['updated_ago_format'] % timeSince(self.i18n,info['date']),
          info['last-modified'],
          self.i18n['updated_ago_format'] % timeSince(self.i18n,info['last-modified'])))
      buffer.append(u"</tbody></table>")
    buffer.append(u"<blockquote><small>%s</small></blockquote>" % (self.i18n['search_instructions']))
    tag.replaceWith(u''.join(buffer))
