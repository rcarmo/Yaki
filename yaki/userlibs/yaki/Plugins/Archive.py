#!/usr/bin/env python
# encoding: utf-8
"""
SyntaxHighlight.py

Created by Rui Carmo on 2008-03-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from BeautifulSoup import *
from yaki.Utils import *
import urllib, time, re

form = u"""
<center>
<form action="%(url)s" method="get">
<select name="year">
%(years)s
</select>
<select name="month">
%(months)s
</select>
<input type="submit" value="%(button)s">
</form>
</center>

%(table)s
"""

monthnames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November","December"]

class ArchiveWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','archive')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    try:
      if not tag['src']:
        tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['error_plugin_attr'])
        return False
      prefix = re.compile(tag['src'])
    except:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['error_plugin_attr'])
      return False

    # if the indexer isn't finished, make sure we fail gracefully
    # TODO: review this for better error handling (see other failure point below)
    if not self.ac.indexer.done:
      tag.replaceWith(self.i18n['warning_message_format'] % self.i18n['indexing_message'])
      return False

    # check cache for results of previous run
    try:
      mtime = self.ac.cache.mtime('archive:' + tag['src'])
      if(mtime > (time.time()-3600)):
        entries = self.ac.cache['archive:' + tag['src']]
      else:
        raise KeyError
    # Build an entry tree if nothing exists
    except KeyError:
      entries = {}
      for name in self.ac.store.allPages():
        try:
          # we're looking for things with a time-based format
          # prefix/YYYY/mm/dd/something
          (namespace,year,month,day) = name.split('/',3)
        except ValueError:
          continue
        if not prefix.match(namespace):
          continue
        if '/' in day:
          (day,dummy) = day.split('/',1)
        if year not in entries.keys():
          entries[year] = {}
        if month not in entries[year].keys():
          entries[year][month] = {}
        if day not in entries[year][month].keys():
          entries[year][month][day] = {}
        try:
          entries[year][month][day][name] = self.ac.indexer.pageinfo[name]
        except KeyError:
          # TODO: this should only happen with new entries found between indexing cycles. Confirm it is so.
          pass
      self.ac.cache['archive:' + tag['src']] = entries
    
    # sanitize query parameters
    y = request.getParameter('year', default=time.strftime("%Y"))
    if y not in entries.keys():
      y = time.strftime("%Y")
    m = request.getParameter('month', default=time.strftime("%m"))
    if m not in entries[y].keys():
      m = time.strftime("%m")
    
    # render controls based on query
    years=[]
    months=[]
    e = entries.keys()
    e.sort()
    for i in e:
      if i == y:
        s = 'selected'
      else:
        s = ''
      years.append('<option %s value="%s">%s</option>' % (s,i,i))
    years = u''.join(years)
    for i in range(12):
      if m == ("%02d" % (i+1)):
        s = 'selected'
      else:
        s = ''
      months.append('<option %s value="%02d">%s</option>' % (s,i+1,self.i18n[monthnames[i]]))
    months = u''.join(months)
    url = "?"
    button = self.i18n['List']
    
    rows = []
    try:
      days = entries[y][m].keys()
    except KeyError: #there are no entries for this year/month
      table = '<div class="warning">%s</div>' % ('There are no entries for %s %s' % (self.i18n[monthnames[int(m)-1]], y))
      buffer = form % locals()
      tag.replaceWith(u''.join(buffer))
      return

    # Render the archive in reverse chronological order
    days.sort()
    days.reverse()
    for d in days:
      e = entries[y][m][d].keys()
      e.sort()
      e.reverse()
      posts = []
      for i in e:
        (namespace,dummy) = i.split('/',1)
        posts.append('<a href="%s">%s</a> <small>(%s)</small><br/>' % (self.ac.base + i,self.ac.indexer.pageinfo[i]['title'],namespace)) #time.strftime("%H:%M",time.localtime(self.ac.indexer.pageinfo[i]['date']))))
      posts = u''.join(posts)[:-5] # append current item trimming trailing <br/>
      rows.append('<tr><td align="center">%s</td><td>%s</td></tr>' % (d,posts))
    rows = u''.join(rows)
    table = '<table width="100%%"><tr><th>%s</th><th>%s</th></tr>%s</table>' % (self.i18n['Day'],self.i18n['Entries'],rows)
    buffer = form % locals()
    tag.replaceWith(u''.join(buffer))
