#!/usr/bin/env python
# encoding: utf-8
"""
Feeds.py

Created by Rui Carmo on 2007-05-11.
Published under the MIT license.
"""

import os, time, cgi, re, urlparse, hashlib
from snakeserver.snakelet import Snakelet
from BeautifulSoup import *
from yaki.Engine import renderPage
from yaki.Store import Store
from yaki.Utils import *
from yaki.Layout import *
import yaki.Locale

try:
  import json
except:
  import simplejson as json

exclusions = ['^HomePage$','^meta.+']

def filtered(name,namespace,exclusions):
  for pattern in exclusions:
    if re.match(pattern, name):
      return False
  if re.match("^%s.+" % namespace, name):
    return True
  return False


class Restyler():
  def __init__(self, buffer):
    self.styles = {}
    soup = BeautifulSoup(buffer)
    self.grabStyles(soup)

  def grabStyles(self,soup):
    styled = soup.findAll(attrs={'style':re.compile('.+')})
    for tag in styled:
      self.styles[tag.name] = tag['style']

  def applyStyles(self,soup):
    for tag in self.styles.keys():
      items = soup.findAll(tag)
      for i in items:
        i['style'] = self.styles[tag]
    return soup


class RSS(Snakelet):
  """
  Feed Generator
  """
  def init(self):
    self.last = 20
    self.ttl = 1800
    self.mimetype = 'application/rss+xml'
    self.escaped = ['description','title','author','category','permalink','link','technorati','footer']

  def sanitizeItem(self,item):
    for field in item.keys():
      if field in self.escaped:
        item[field] = cgi.escape(item[field])
    return item
  
  def getDescription(self):
    return "RSS Feed Generator"

  def allowCaching(self):
    return False
    
  def requiresSession(self):
    return self.SESSION_NOT_NEEDED
  
  def filterRecent(self, request):
    a = request.getWebApp()
    ac = a.getContext()
    filter = ''
    if '+' in self.namespace:
      for part in self.namespace.split('+'):
        if part in ac.namespaces:
          filter = filter + part + "|"
      filter = "^(%s)" % filter[:-1]
    elif self.namespace not in ac.namespaces:
      filter = '.+'
      self.namespace = 'wiki'
    else:
      filter = self.namespace
    recent = [x for x in ac.indexer.recent if filtered(x,filter,exclusions)]
    return recent
  
  def checkCache(self, request, response):
    a = request.getWebApp()
    ac = a.getContext()
    now = time.time()

    # Try to use the main site URL to avoid trouble with reverse proxying and port numbers
    try:
      self.siteurl = ac.siteinfo['siteurl'] 
    except:
      self.siteurl = request.getBaseURL()
    self.baseurl = self.siteurl + ac.base
    # pattern is /feeds/filter
    try:
      (dummy,self.namespace) = request.getFullQueryArgs().split('/',1)
    except:
      response.setResponse(404, "Not Found")
      return
    try:
      if (now - ac.cache.mtime('feeds:' + self.namespace + self.mimetype + self.rewritelinks)) < self.ttl:
        # TODO: add compression
        response.setHeader("Content-Type", mimetype)
        response.getOutput().write(ac.cache['feeds:' + self.namespace + self.mimetype + self.rewritelinks])
        return
    except:
      pass
  
  def buildItems(self, recent, request):
    a = request.getWebApp()
    ac = a.getContext()
    i18n = yaki.Locale.i18n[ac.locale]
    
    items = []

    i = 1
    for pagename in recent:
      restyler = Restyler(ac.templates['rss-styles'])
      try:
        page = ac.store.getRevision(pagename)
      except:
        continue # loop if a page goes missing
      try:
        headers = ac.indexer.pageinfo[pagename]
      except:
        headers = page.headers
      # skip non-indexable pages (no point in adding those to a feed)
      if "x-index" in headers:
        if headers["x-index"].lower() == "no":
          continue
      if "title" in headers:
        title = headers['title']
      else:
        title = pagename
      soup = restyler.applyStyles(BeautifulSoup(renderPage(ac, page)))
      technorati = technoratiTags(headers,soup)
      self.handleMedia(soup)
      description = unicode(soup)
      pubdate = httpTime(headers['last-modified'])
      origdate = plainDate(i18n,headers['date'])
      updated = not (headers['last-modified'] == headers['date'])
      if hasComments(ac,pagename):
        comments = i18n['rss_comments_allowed']
      else:
        comments = ""
      if "x-link" in headers and self.rewritelinks == 'x-link':
        link = headers['x-link']
        permalink = guid = self.baseurl + pagename.replace(' ','_')
      else:
        permalink = link = guid = self.baseurl + pagename.replace(' ','_')
        
      if re.compile('^(%s|links)' % ac.siteinfo['journal']).match(pagename):
        permalink = permalink + "#%s" % sanitizeTitle(title)
      
      guid = ac.siteinfo['siteurl'].replace("http://","") + "." + hashlib.sha1(guid).hexdigest()
      category = self.namespace
      author = headers['from']
      enclosure = ''
      if "x-enclosure" in headers:
        basename = headers['x-enclosure'].strip()
        filename = ac.store.getAttachmentFilename(pagename,basename)
        if os.path.exists(filename):
          enclosure = '<enclosure url="%s" length="%d" type="%s"/>' % (cgi.escape(self.siteurl + ac.media + pagename + "/" + basename), os.stat(filename).st_size, response.guessMimeType(filename))
      siteurl = self.siteurl
      sitetitle = ac.siteinfo['sitetitle']
      sitedescription = ac.siteinfo['sitedescription']
      items.append({'pagename':pagename, 'siteurl':siteurl, 'sitetitle':sitetitle, 'sitedescription':sitedescription, 'title':title, 'description':description, 'technorati':technorati, 'pubdate':pubdate, 'origdate':origdate, 'comments':comments, 'permalink':permalink, 'link':link, 'guid':guid, 'category':category, 'author':author, 'guid':guid, 'enclosure':enclosure, 'updated':updated})
      i = i + 1
      if i > self.last:
        break
    info = ac.siteinfo
    return items
  
  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    a = request.getWebApp()
    ac = a.getContext()
    s = self.getContext()
    print "Serving RSS feed %s to %s (%s)" % (os.path.dirname(request.getRequestURL()), request.getRealRemoteAddr(), request.getUserAgent())
    try:
      self.rewritelinks = a.getConfigItem('feedbehavior')[os.path.dirname(request.getRequestURL())]
    except:
      self.rewritelinks = 'x-link'
     
    # locals used by main template
    sitetitle = ac.siteinfo['sitetitle']
    sitedescription = ac.siteinfo['sitedescription']
    self.checkCache(request, response)
    builddate = pubdate = httpTime(time.time())
    rawitems = self.buildItems(self.filterRecent(request), request)
    siteurl = self.siteurl
    
    items = []
    for item in rawitems:
      if item['updated']:
        item['description'] = (ac.templates['rss-item-update'] % item) + item['description']
      if not re.match('^links', item['pagename']):
        item['footer'] = ac.templates['rss-footer'] % item
      else:
        item['footer']=''
      items.append(ac.templates['rss-item'] % self.sanitizeItem(item))
    
    if not ac.indexer.done:
      items = ''
      buffer = ac.templates['rss-feed'] % locals()
    else:
      items = ''.join(items)
      buffer = ac.templates['rss-feed'] % locals()
      ac.cache['feeds:' + self.namespace + self.mimetype + self.rewritelinks] = buffer
    # TODO: add compression
    response.setHeader("Content-Type", self.mimetype)
    response.getOutput().write(buffer)
  
  
  def handleMedia(self, soup):
    # make all wiki and image URLs absolute
    links = soup.findAll('a') #links = soup.findAll('a',{'class':re.compile('wiki.*')}) would find all wiki links, but we want all of them   
    for link in links:
      try:
        (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(link['href'])
        if schema == '': # assume these are relative links inside this site
          link['href'] = self.siteurl + link['href']
      except KeyError:
        pass
    images = soup.findAll('img')
    for image in images:
      image['src'] = self.siteurl + image['src']      
    # remove all scripting
    [script.extract() for script in soup.findAll('script')]
    

class JSON(RSS):
  """
  Feed Generator
  """
  
  def init(self):
    self.last = 20
    self.ttl = 1800
    self.mimetype = 'application/json'
    self.escaped = ['description','title','author','category','permalink','link','footer']


  def getDescription(self):
    return "JSON Feed Generator"
    
  def sanitizeItem(self,item):
    media = []
    for field in item.keys():
      if field in self.escaped:
        soup = BeautifulSoup(item[field])
        if field == 'description':
          images = soup.findAll('img')
          for image in images:
            media.append(image['src'])
        #plaintext = u' '.join(soup.findAll(text=re.compile('.*'))).strip()
        plaintext = re.sub(r'<[^>]*?>', '', item[field]).strip()
        item[field] = plaintext.replace('"','\"')
      item['images'] = str(media).replace("'",'"')
    return item
    
  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    a = request.getWebApp()
    ac = a.getContext()
    s = self.getContext()
     
    # locals used by main template
    sitetitle = ac.siteinfo['sitetitle']
    sitedescription = ac.siteinfo['sitedescription']
    self.checkCache(request, response)
    builddate = pubdate = httpTime(time.time())
    rawitems = self.buildItems(self.filterRecent(request), request)
    siteurl = self.siteurl
    
    items=[]
    for item in rawitems:
      items.append(ac.templates['json-item'] % self.sanitizeItem(item))
    
    if not ac.indexer.done:
      items = ''
      buffer = '[' + ','.join(items) + ']'
    else:
      buffer = '[' + ','.join(items) + ']'
      ac.cache['feeds:' + self.namespace + self.mimetype + self.rewritelinks] = buffer
    # TODO: add compression
    response.setHeader("Content-Type", self.mimetype)
    response.getOutput().write(buffer)

  
