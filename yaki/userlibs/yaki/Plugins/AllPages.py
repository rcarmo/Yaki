#!/usr/bin/env python
# encoding: utf-8
"""
AllPages.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import re

try:
  import cPickle as pickle
except ImportError:
  import pickle # fall back on Python version


class AllPagesWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','AllPages')
    self.ac = webapp.getContext()
    self.cache = self.ac.cache
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    titles = {"@":[],"0-9":[]}
    titlePrefix = re.compile('^((%s) )(.+)' % self.i18n['index_prefix_regex'])
    pathPrefix = re.compile('^((%s)/)(.+)' % '|'.join(self.ac.namespaces))
    alpha = re.compile('^[a-zA-Z]')
    digit = re.compile('^[0-9]')
    for name in self.ac.indexer.pageinfo.keys():
      page = self.ac.indexer.pageinfo[name]
      # Re-order title text to make it easier to sort
      title = page['title']
      if titlePrefix.match(title):
        title = titlePrefix.sub("\\3, \\2", title)
      if pathPrefix.match(name):
        title = title + " <small>(%s)</small>" % pathPrefix.match(name).groups(2)[1]
      initial = title[0].upper()
      entry = {'name':name, 'title':title, 'mtime':page['last-modified']}
      if alpha.match(initial):
        if initial not in titles.keys():
          titles[initial] = [entry]
        else:
          titles[initial].append(entry)
      elif digit.match(initial):
        titles['0-9'].append(entry)
      else:
        titles['@'].append(entry)

    order = titles.keys()
    order.sort()
    
    buffer = []
    for i in order:
      buffer.append('<a href="%s#_%s">%s</a>&nbsp;' % (self.ac.base + pagename,i,i))
    header = ''.join(buffer)
    buffer = []
    buffer.append('<table width="100%">')
    buffer.append('<tr><th colspan=2>%s</th></tr>' % header)
    counter = 1
    for letter in order:
      if titles[letter] != []:
        if (counter % 2):
          buffer.append('<tr>')
        # sort title information
        titles[letter].sort(lambda x, y:cmp(x['title'],y['title']))
        entry = []
        for page in titles[letter]:
          entry.append('<a href="%s" title="%s">%s</a><br/>' % (self.ac.base + page['name'],self.i18n['updated_ago_format'] % timeSince(self.i18n, page['mtime']),page['title']))
        buffer.append('<td valign="top"><a name="_%s"><h2>%s</h2></a>%s</td>' % (letter,letter,''.join(entry)))
        counter = counter + 1
        if (counter % 2):
          buffer.append('</tr>')
    buffer.append('</table>')
    tag.replaceWith(''.join(buffer))

