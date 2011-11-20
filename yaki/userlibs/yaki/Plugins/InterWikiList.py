#!/usr/bin/env python
# encoding: utf-8
"""
InterWikiList.py

Created by Rui Carmo on 2008-03-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import urllib

class InterWikiListWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','interwiki')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    if not self.ac.indexer.done:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['indexing_message'])
      return False
    
    buffer = [u'<table class="compact"><thead><tr><th>%s</th><th>%s</th></tr></thead><tbody>' % (self.i18n['Item'],self.i18n['References'])]
    try:
      schema = tag['src'].lower() # grab the interwiki schema from the src attribute in the plugin tag
    except:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['error_plugin_attr'])
      return False

    try:
      if schema not in self.ac.indexer.interwikilinks.keys():
        # TODO: create specific error message
        tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['error_plugin_attr'])
        return False
      data = self.ac.indexer.interwikilinks[schema]
    except:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['indexing_message'])
      return False
    
    pageinfo = self.ac.indexer.pageinfo
    items = data.keys()
    # sort items by increasing timestamp of modification time
    # TODO: review this sort order, which might not make sense for all purposes
    items.sort(lambda b, a: cmp(data[a]['mtime'], data[b]['mtime']))
    for item in items:
      link = data[item]
      link['rel'] = "%s:%s" % (schema,item)
      try:
        row = [u'<tr><td><a href="%(href)s" title="%(title)s" rel="%(rel)s" class="interwiki">%(text)s</a></td><td class="referring_urls">' % link]
        references = link['pages']
        references.sort(lambda b, a: cmp(pageinfo[a]['last-modified'], pageinfo[b]['last-modified']))
        for reference in references:
          row.append(u'<a href="%s" title="%s">%s</a><br/>' % (self.ac.base + reference, self.i18n['updated_ago_format'] % timeSince(self.i18n, pageinfo[reference]['last-modified']), pageinfo[reference]['title']))
        buffer.append(u''.join(row)[:-5]) # append current partial row trimming trailing <br/>
        buffer.append(u'</td></tr>')
      except:
        print "INFO: Error in InterWikiListWikiPlugin for %s" % item
    buffer.append(u'</tbody></table>')
    tag.replaceWith(u''.join(buffer))
