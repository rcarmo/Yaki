#!/usr/bin/env python
# encoding: utf-8
"""
LinkBlog.py

Created by Rui Carmo on 2007-09-18.
Published under the MIT license.
"""

# standard libraries
import os, sys, time, calendar, threading, rfc822, urlparse, urllib, re, stat, cgi, tempfile

# backwards compatibility
try:
  import json
except:
  import simplejson as json

# userlibs
import feedparser, expander, fetch
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

# Snakelets logging
import logging
log=logging.getLogger("Snakelets.logger")

# yaki
from yaki.Page import Page
from yaki.Store import Store
from yaki.Utils import *
from yaki.Layout import *
import yaki.Plugins
import yaki.Locale

try:
  # Check for webthumb functionality
  import webthumb
  thumbnails = True
except ImportError:
  thumbnails = False

class Importer(threading.Thread):
  """
  Link blog
  """
  
  def __init__(self,webapp):
    self.webapp = webapp
    threading.Thread.__init__(self)
    try:
      delicious = self.webapp.getConfigItem('linkblog')
      self.url = delicious['url']
      self.authors = delicious['authors']
      self.format = delicious['format']
      self.thumbs = {}
      log.info("Retrieval active")
    except:
      log.warning("Invalid or missing settings, retrieval inactive")
      self.working = False
      return
    if thumbnails:
      self.apikey = self.webapp.getConfigItem('services')['webthumb']['apikey']
    self.working = True

  def stop(self):
    self.working = False

  def run(self):
    if not self.working:
      return
    # Wait for 30s before starting
    for i in range(0, 6):
      time.sleep(5)
      if not self.working:
        log.debug("Terminating fetcher before first fetch.")
        return
    # Play nice and allow for thread to be killed externally with minimum delay
    while(self.fetchLinks()):
      for i in range(0, 15):
        time.sleep(120)
        self.checkThumbnails()
        if not self.working:
          log.info("Terminating fetcher.")
          return

  def checkThumbnails(self):
    ac = self.webapp.getContext()
    siteurl = ac.siteinfo['siteurl'] + ac.base
    for uri in self.thumbs.keys():
      page = self.thumbs[uri]['page']
      count = self.thumbs[uri]['count']
      data = self.thumbs[uri]['data']

      # check for invalid or stalled entries in list
      if self.thumbs[uri]['thumb'] is None or count > 20:
        log.warning("Thumbnail for %s could not be retrieved (tried %d times)." % (uri, count))
        try:
          ac.notifier.send(self.webapp.getConfigItem('jid'), "Thumbnail for %s could not be retrieved (tried %d times)." % (uri, count))
          ac.notifier.send(self.webapp.getConfigItem('jid'), "Stored entry %s without thumbnail" % (siteurl + page))
        except:
          pass
        ac.store.updatePage(page,data)
        del self.thumbs[uri] # remove from list
      else:
        key = self.thumbs[uri]['thumb']['key']
        log.debug("Trying to obtain thumbnail for %s" % key)
        thumbnail = tempfile.mktemp(dir='/tmp')
        # try getting the medium thumbnail first
        if webthumb.get_thumbnail(self.apikey,key,thumbnail,'medium'):
          ac.store.addAttachment(page,thumbnail,'thumbnail.jpg')
          template = 'linkblog-with-thumbnail'
          thumbnail = tempfile.mktemp(dir='/tmp')
          # large thumbnail should be done at the same time...
          if webthumb.get_thumbnail(self.apikey,key,thumbnail,'large'):
            ac.store.addAttachment(page,thumbnail,'large.jpg')
            # ...but we upgrade the template only if it is
            template = 'linkblog-with-quicklook'
          # this runs the existing content through the template
          data['content'] = ac.templates[template] % data
          ac.store.updatePage(page,data)
          del self.thumbs[uri] # remove from list
          log.info("Stored entry %s using %s" % (page,template))
          try:
            ac.notifier.send(self.webapp.getConfigItem('jid'), "Stored linkblog entry %s" % (siteurl + page))
          except:
            pass
          try:
            ac.twitter.send(siteurl + page, data['title'])
          except:
            log.warning("Unable to send Twitter update for %s" % page)
            pass
        else:
          count = count + 1
          self.thumbs[uri]['count'] = count

  def queueThumbnail(self, uri, page, data):
    thumbnail = None    
    if uri not in self.thumbs.keys():
      key = webthumb.submit_job(self.apikey, cgi.escape(uri))
      if key is not None:
        self.thumbs[uri] = {'page':page, 'data':data, 'thumb':key, 'count': 0}
      else:
        log.warning("Could not queue thumbnail for %s" % uri)
        return False
    return True

  def assembleItem(self, fields):
    # remove some tags
    remove = ['for:links','post:links','comments:on', 'comments:off']
    store = self.webapp.getContext().store
    e = expander.URLExpander()
    uri = e.query(fields['uri'])
    comments = 'Off' # sensible default for linkblog
    if 'comments:on' in fields['tags']:
      comments = 'On'
    elif 'comments:off' in fields['tags']:
      comments = 'Off'
    _headers = "X-Comments: %s\nX-Link: %s" % (comments, uri)
    date = time.strftime("%Y-%m-%d %H:%M:%S", fields['when'])
    tags = ', '.join([x for x in fields['tags'].split(' ') if x not in remove])
    keywords = tags = tags.replace(',,',',') # remove double commas
    page = time.strftime("links/%Y/%m/%d/%H%M", fields['when'])
    categories = "Links"
    markup = self.webapp.getConfigItem('defaultmarkup')
    fields.update(locals())
    # filter fields to grab only the relevant data
    data = dict([(k,v) for k,v in fields.items() if k in ['author','date','markup','title','keywords','categories','tags','_headers','content']])
    # Does the page exist already?
    if not store.mtime(page):
      # remove some del.icio.us tags
      remove = ['for:links','post:links','comments:on', 'comments:off']
      comments = 'Off' # sensible default for linkblog
      if 'comments:on' in fields['tags']:
       comments = 'On'
      elif 'comments:off' in fields['tags']:
        comments = 'Off'
      e = expander.URLExpander()
      uri = e.query(fields['uri'])
      log.debug("Expanding %s for %s: got %s" % (fields['uri'], page, uri))
      (schema, netloc, path, params, query, fragment) = urlparse.urlparse(uri)
      if schema not in ['http', 'https']: # last ditch check for broken delicious feeds
        log.error("Expanding %s: got %s" % (fields['uri'], uri))
        return
      _headers = "X-Comments: %s\nX-Link: %s" % (comments, uri)
      date = time.strftime("%Y-%m-%d %H:%M:%S", fields['when'])
      tags = ', '.join([x for x in fields['tags'].split(' ') if x not in remove])
      keywords = tags = tags.replace(',,',',') # remove double commas
      categories = "Links"
      markup = self.webapp.getConfigItem('defaultmarkup')
      fields.update(locals())
      # filter fields to grab only the relevant data
      data = dict([(k,v) for k,v in fields.items() if k in ['author','date','markup','title','keywords','categories','tags','_headers','content']])
      if thumbnails:
        if self.queueThumbnail(uri,page,data):
          pass
        else:
          store.updatePage(page,data)
      else:
        store.updatePage(page,data)    

  def fetchLinks(self):
    ac = self.webapp.getContext()
    # Do not run fetcher in staging mode
    if ac.staging:
      return
    
    # use our own fetcher for centralized debugging (if necessary)
    log.info("Fetching feed %s" % self.url)
    result = fetch.fetchURL(self.url)

    if self.format == 'rss':
      data = feedparser.parse(result['data'])
      for item in data.entries:
        try: 
          author = self.authors[item.author]
        except:
          author = self.webapp.getConfigItem('author')
        #try:
        when = time.localtime(calendar.timegm(item.updated_parsed))
        uri = item.link
        title = item.title
        content = converthtml(item.description.replace("#x26;",""))
        #soup = BeautifulSoup(item.description, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
        tags = ' '.join([tag['term'] for tag in item.tags])
        self.assembleItem(locals())
        #except:
        #  pass
    #elif self.format == 'greadernotes':
    #  TODO: implement Google Reader note parsing (getting tags from original item, etc.)
    #  pass
    elif self.format == 'json':
      nuts = json.loads(result['data'])
      for item in nuts['value']['items']:
        try: 
          author = self.authors[item['dc:creator']]
        except:
          author = self.webapp.getConfigItem('author')
        try:
          when = time.strptime(item['dc:date'],'%Y-%m-%dT%H:%M:%SZ')
          uri = item['rdf:about']
          title = item['title']
          content = item['description']
          tags = item['dc:subject'].lower()
          self.assembleItem(locals())
        except:
          pass
    log.info("Fetch and processing completed")
    return True
