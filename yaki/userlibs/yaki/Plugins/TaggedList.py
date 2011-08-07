#!/usr/bin/env python
# encoding: utf-8
"""
TaggedList.py

Created by Rui Carmo on 2008-04-19.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import urllib

class TaggedListWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','tagged')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    if not self.ac.indexer.done:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['indexing_message'])
      return False
    
    buffer = [u'<table class="compact"><thead><tr><th>%s</th><th>%s</th></tr></thead><tbody>' % (self.i18n['Created'],self.i18n['Title'])]
    try:
      if tag['title'].lower() == 'no':
        buffer = [u'<table class="compact borderless"><tbody>']
    except:
      pass

    try:
      wantedtag = tag['src'].lower() # grab the tag name
    except:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['error_plugin_attr'])
      return False

    try:
      if wantedtag not in self.ac.indexer.tags.keys():
        # TODO: create specific error message
        tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['error_plugin_attr'])
        return False
      items = self.ac.indexer.tags[wantedtag]    
    except:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['indexing_message'])
      return False
    
    pageinfo = self.ac.indexer.pageinfo
    # sort items by increasing timestamp of creation time
    items.sort(lambda a, b: cmp(pageinfo[a]['date'], pageinfo[b]['date']))
    for item in items:
      try:
        buffer.append(u'<tr><td>%s' % plainTime(self.i18n, pageinfo[item]['date']))
        buffer.append(u'</td><td><a href="%s">%s</a></td></tr>' % (self.ac.base + item, pageinfo[item]['title']))
      except:
        print "INFO: Error in TaggedListWikiPlugin for %s" % pagename
    buffer.append(u'</tbody></table>')
    tag.replaceWith(u''.join(buffer))
