#!/usr/bin/env python
# encoding: utf-8
"""
Journal.py

Created by Rui Carmo on 2006-12-16.
Published under the MIT license.
"""

import re, md5, urlparse, time, cgi, traceback
import yaki.Engine, yaki.Store, yaki.Locale
from yaki.Utils import *
from yaki.Layout import *
from BeautifulSoup import *

import logging
log=logging.getLogger("Snakelets.logger")

# the meta page from where we'll get hand-picked highlights to render some simple HTML
# that the site theme will then display on the sidebar
metaPage = "meta/Highlights" 

class JournalWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','Journal')
    self.webapp = webapp
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]

  def run(self, serial, tag, tagname, pagename, soup, request, response): 
    ac = self.ac
    c = request.getContext()
    # define how many blog entries to show
    try:
      bound = int(tag['limit'])
    except:
      bound = 12
    # filter for the namespaces to be shown on the home page
    mask = re.compile('^(%s|links|podcast)\/(\d+){4}\/(\d+){2}\/(\d+){2}.*' % ac.siteinfo['journal'])
    # this is what entries ought to look like, ideally
    canon = "0000/00/00/0000"
    
    # find entries. 
    # We use the indexer's allpages here because that's updated upon server start
    # ...and because we want to do our own sorting anyway.
    paths = [path for path in self.ac.indexer.allpages if mask.match(path)]
    # canonize paths
    entries = {}
    for i in paths:
      (prefix, path) = i.split("/",1)
      l = len(path)
      p = len(prefix)+1
      k = len(canon)
      # add an hex digest in case there are multiple entries at the same time
      if l < k:
        entries[i[p:l+p] + canon[-(k-l):] + md5.new(i).hexdigest()] = i
      else:
        entries[i[p:] + md5.new(i).hexdigest()] = i

    journal = entries.keys()
    journal.sort()
    journal.reverse()
    journal = journal[:bound]
    posts = []
    prevdate = ""
    for i in journal:
      dateheading = i[:10]
      if dateheading != prevdate:
        date = time.strptime(dateheading, '%Y/%m/%d')
        posts.append('<h3 class="dateheading">%s</h3>' % plainDate(self.i18n,date))
        prevdate = dateheading
      name = entries[i]
      try:
        page = ac.store.getRevision(name)
      except IOError:
        log.error("Journal: could not retrieve %s" % name)
        continue  
      headers = page.headers
      path = ac.base + name
      linkclass = "wikilink"
      posttitle = headers['title']
      rellink = path
      #permalink = headers['bookmark'] = request.getBaseURL() + rellink
      permalink = headers['bookmark'] = rellink
      if re.compile('^(%s|links)' % ac.siteinfo['journal']).match(name):
        permalink = permalink + "#%s" % sanitizeTitle(posttitle)
      description = "permanent link to this entry"
      if 'x-link' in headers.keys():
        link = uri = headers['x-link']
        (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
        if schema in self.i18n['uri_schemas'].keys():
          linkclass   = self.i18n['uri_schemas'][schema]['class']
          description = "external link to %s" % cgi.escape(uri)
      content = yaki.Engine.renderPage(self.ac,page)#, cache=False)
      postinfo = renderInfo(self.i18n,headers)
      metadata = renderEntryMetaData(self.i18n,headers)
      # Generate c.comments
      formatComments(ac,request,name, True)
      comments = c.comments
      try:
        tags = headers['tags']
      except:
        tags = ""
      
      references = ''
      if 'links' in name:
        posts.append(ac.templates['linkblog'] % locals())
      else:
        posts.append(ac.templates['journal'] % locals())
    try:
      self.loadHighlights()
      log.info("Highlights loaded.")
    except Exception, e:
      log.error("Error loading highlights: %s" % e)
      pass
    tag.replaceWith(''.join(posts))

  def loadHighlights(self):
    # load Highlighted page list
    try:
      page = self.ac.store.getRevision(metaPage)
    except:
      log.warning("%s missing - no highlights loaded." % metaPage)
      return
    self.highlights = {}
    soup = BeautifulSoup(page.render())
    sections = [(x.findPreviousSiblings('h1')[0].string, x.string) for x in soup.findAll("pre")]
    buffer = []
    for s in sections:
      section = []
      (heading,pages) = s
      section.append("<li><dt>%s</dt><ul>\n" % heading)
      pages = pages.split('\n')
      for page in pages:
        try:
          (page, title) = page.strip().split(' ',1)
        except ValueError: # try to fetch titles for pages without them
          page = page.strip()
          try:
            title = self.ac.indexer.pageinfo[page]['title']
          except:
            continue
        if page in self.ac.indexer.aliases.keys():
          section.append("""<li><a href="%s">%s</a></li>\n""" % (self.ac.base + page,title))
        else:
          section.append("""<li><a href="%s">%s</a></li>\n""" % (page,title))
      section.append("</ul></li>\n")
      if len(section) > 2: # if we got more than just the close and end tags
        buffer.append(''.join(section))
    self.buffer = ''.join(buffer)
    self.ac.highlights = self.buffer