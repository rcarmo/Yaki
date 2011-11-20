#!/usr/bin/env python
# encoding: utf-8
"""
Engine.py

Created by Rui Carmo on 2006-08-19.
Published under the MIT license.
"""

from snakeserver.snakelet import Snakelet
import os, sys, time, rfc822, unittest, urlparse, urllib, re, stat, cgi
import fetch, simplejson
from sets import Set
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from yaki.Page import Page
from yaki.Store import Store, BASE_FILENAME
from yaki.Cache import Cache
from yaki.Utils import *
from yaki.Layout import *
import yaki.Plugins
from yaki.Locale import *

# try to speed up pickle if possible
try:
  import cPickle as pickle
except ImportError: # fall back on Python version
  import pickle 

def renderReferences(ac,headers):
  buffer = []
  if not ac.indexer.done:
    return ""
  if ['references'] in headers.keys():
    thread = {}
    for page in headers['thread'].split(','):
      page = page.strip()
      try:
        date = ac.indexer.pageinfo[page]['date']
        title = ac.index.pageinfo[page]['title']
        thread[date] = {'item':page,'title':title}
      except:
        pass
    linear = [date for date in thread.keys()]
    linear.sort()
    prev = next = None
    for i in linear:
      if i < headers['date']:
        prev = i
      if i > headers['date']:
        next = i
        break
    if prev:
      buffer.append('<div class="nav_prev_article"><a href="%s">%s</a></div>' % (ac.base + thread[prev]['page'], shrink(thread[prev]['title'],20)))
    if next:
      buffer.append('<div class="nav_next_article"><a href="%s">%s</a></div>' % (ac.base + thread[next]['page'], shrink(thread[next]['title'],20)))
  return ''.join(buffer)

def subRender(c,page,request,response,indexing):
  soup = BeautifulSoup(page.render(c.defaultmarkup), selfClosingTags=['plugin'],convertEntities=['html','xml'])
  for tag in soup('plugin'):
    c.plugins.run(tag, 'plugin', page.headers['name'], soup, request, response, indexing)
  c.plugins.runForAllTags(page.headers['name'], soup, request, response, indexing)
  return soup.renderContents().decode('utf-8')


def renderPage(c, page, request = None, response = None, cache = True, indexing = False):
  """Auxiliary function invoked from Indexer and Engine"""
  if request is None:
    # page rendered within a feed or batch context
    key = "soup:" + '_' + page.headers['name']
  else:
    # page rendered for online viewing or indexing
    key = "soup:" + page.headers['name']
  if not cache:
    return subRender(c,page,request,response,indexing)
  else:
    if "x-cache-control" in page.headers.keys():
      control = page.headers["x-cache-control"].lower()
      m = MAX_AGE_REGEX.match(control)
      if m:
        seconds = int(m.group(3))
        try:
          if (c.cache.mtime(key) + seconds) < time.time():
            del(c.cache[key])
        except KeyError:
          pass
    try:
      if c.store.mtime(page.headers['name']) > c.cache.mtime(key):
        del(c.cache[key])
        raise KeyError
      else:
        return c.cache[key]
    except KeyError:
      c.cache[key] = buffer = subRender(c,page,request,response,indexing)
    return buffer
  # end else

class Attachment(Snakelet):
  """Attachment requests"""
  def getDescription(self):
    return "Wiki Attachment Locator"

  def allowCaching(self):
    return False # we want to handle it ourselves
    
  def requiresSession(self):
    return self.SESSION_NOT_NEEDED
  
  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    a = self.getWebApp()
    c = request.getContext()
    c.fullurl = request.getBaseURL() + request.getFullQueryArgs()
    path = urllib.unquote((request.getPathInfo())[1:])
    (page,attachment) = os.path.split(path)
    if attachment != BASE_FILENAME:
      c = self.getAppContext()
      filename = c.store.getAttachmentFilename(page,attachment)
      if os.path.exists(filename):
        stats = os.stat(filename)
        response.setHeader("Cache-Control",'max-age=86400')
        response.setHeader("Expires", httpTime(time.time() + 86400))
        (etag,lmod) = a.create_ETag_LMod_headers(stats.st_mtime, stats.st_size, stats.st_ino)
        response.setHeader("Last-Modified", lmod)
        response.setHeader("Etag", etag)
        a.serveStaticFile(filename, response, useResponseHeaders=False)
    response.setResponse(404, "Not Found")
    return None

class Starting(Exception):
  print "Server starting..."
  pass

class Wiki(Snakelet):
  """Wiki Engine"""
  def getDescription(self):
    return "Wiki Engine"

  def allowCaching(self):
    return False # we want to handle it ourselves

  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    ac = self.getAppContext()
    a = self.getWebApp()
    if ac.indexer.ready != True:
      #print "redirecting"
      ac = request.getContext()
      response.setHeader("X-Dialtone",'Busy, Please Hold')
      raise Starting
      #self.redirect('/error.y', request, response)
      return
    
    c = request.getContext()
    c.fullurl = request.getBaseURL() + request.getFullQueryArgs()
    self.i18n = yaki.Locale.i18n[ac.locale]
    try:
      # parse page name out of URL
      c.path = unicode((request.getPathInfo())[1:],'latin-1')
      
      # If there was no specific page requested, then render the HomePage
      if c.path == '':
        c.path = 'HomePage'
      
      # Get the actual page contents
      page = self.getPage(request, response)
      # Try to fail gracefully ASAP
      if page == None:
        return
        #out = response.getOutput()
        #print >>out,""
        #return

      (c.headers, c.content) = page
      c.title = c.headers['title']
      c.postinfo = renderInfo(self.i18n, c.headers)
      author = c.headers['from']
      created = plainTime(self.i18n, c.headers['date'], False)
      if c.headers['date'] == c.headers['last-modified']:
        updated = self.i18n['never']
      else:
        updated = plainTime(self.i18n, c.headers['last-modified'], False)      
      
      # Manage page trail (breadcrumbs) 
      r = request.getSessionContext()
      if r is not None:
        try:
          if c.headers['name'] not in r.trail:
            r.trail.append(c.headers['name'])
          if len(r.trail) > 10:
            r.trail = r.trail[-10:]
        except:
          r.trail = [c.headers['name']]
      try:
        trail = []
        for crumb in r.trail:
          info = ac.indexer.pageinfo[crumb]
          # add absolute URL prefix to link
          info['link'] = ac.base + info['name']
          trail.append(info)
        c.trail = '<p>' + self.i18n['pagetrail'] + ': ' + pagetrail(trail[-10:]) + '</p>'
      except:
        c.trail = ''
      
      references = {}
      c.seealso = ""
      try:
        links = ac.indexer.backlinks[c.headers['name']]
        links.extend(ac.indexer.wikilinks[c.headers['name']])
        unique = Set(links)
        links = [unique.pop() for i in range(0,len(unique))]
        if len(links) > 0:
          for link in links:
            # TODO: check ac.base here
            references[ac.base+link] = ac.indexer.pageinfo[link]
          c.seealso = "<p>%s</p>" % self.i18n['seealso'] + seeAlsoLinkTable(self.i18n,references)  
      except KeyError:
        c.seealso = '<div class="warning">' + self.i18n['indexing_message'] + '</div>'
          
      maxage = self.getWebApp().getConfigItem('maxage')
      if 'x-cache-control' in c.headers.keys():
        c.cachecontrol = "public, " + c.headers['x-cache-control']
        m = MAX_AGE_REGEX.match(c.headers['x-cache-control'])
        if m:
          maxage = int(m.group(3))
      
      # The Answer, obviously
      response.setHeader("X-Answer",'42')
      
      # Use cache metadata to generate HTTP headers
      # c.etag, etc. are sent to the template
      try:
        stats = ac.cache.stats("soup:"+c.path)
        (c.etag,c.lastmodified) = a.create_ETag_LMod_headers(stats[0], stats[1], stats[2]) 
      except:
        response.setHeader("X-Answer",'Cache error')
        c.etag = ''
        c.lastmodified =  httpTime(time.time())
        c.cachecontrol = ''
      
      # If we're not running indexing, then pages should be cached a bit longer
      if ac.indexer.done:
        c.expires = httpTime(time.time() + maxage)
      else:
        c.expires = httpTime(time.time())
            
      # Generate c.comments (nasty side-effect, I know...)
      formatComments(ac,request,c.path)

      posttitle = c.title
      permalink = plainpermalink = u"%s%s" % (ac.base, c.path)
      description = self.i18n['permalink_description']
      c.headers['bookmark'] = request.getBaseURL() + permalink
      if SANITIZE_TITLE_REGEX.match(c.path):
        permalink = permalink + u"#%s" % sanitizeTitle(c.title)
      linkclass = "wikilink"
      # Insert outbound links if necessary
      if "x-link" in c.headers:
        uri = c.headers['x-link']
        (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
        permalink = uri
        #posttitle = self.i18n[schema]['title'] % {'uri':uri}
        linkclass   = self.i18n['uri_schemas'][schema]['class']
        description = self.i18n['external_link_format'] % cgi.escape(uri)

      # Prepare other data that needs to be inserted in templates
      if "tags" in c.headers:
        tags = c.headers['tags']
      else:
        tags = ''
      c.keywords = tags # TODO: add more semantic data here
      postinfo = c.postinfo
      content = c.content
      comments = c.comments
      if c.path[:4] == 'meta' or 'x-hide-metadata' in c.headers.keys():
        date = "&nbsp;"
        metadata = ''
      else:
        date = plainDate(self.i18n, c.headers['date'])
        metadata = renderEntryMetaData(self.i18n,c.headers,False)
      references = ''
      # Use a simplified format for the HomePage (less cruft)
      if c.path == "HomePage":
        c.postbody = ac.templates['simplified'] % locals()
      else:
        c.postbody = ac.templates['generic'] % locals()
      c.sitename = ac.siteinfo['sitename']
      c.sitedescription = ac.siteinfo['sitedescription']
      # Output page. Remember that c.stuff goes in as Request parameters
      self.redirect('/wiki.y', request, response)
    except Warning, e:
      c.status = e.value
      (c.headers, c.content) = self.getPage(request, response)
      self.redirect('/wiki.y', request, response)
  
  def requiresSession(self):
    return self.SESSION_WANTED
  
  def dumpTable(self, request):
    h=request.getAllHeaders()
    buffer = '<table class="data">'
    i=0
    for k, v in  h.items():
      style = ('',' class="odd"')[i%2]
      buffer = buffer + '<tr><td%s>%s</td><td%s>%s</td></tr>' % (style, k, style, v)
      i = i + 1
    buffer = buffer + '</table>'
    return buffer
  
  def getMarkup(self, request, response):
    path = (request.getPathInfo())[1:]
    c = self.getAppContext()
    try:
      page = c.store.getRevision(path)
    except:
      page = c.store.getRevision("meta/EmptyPage")
    buffer = page.body
    return buffer
  
  def getPage(self, request, response):
    """TODO: Change this to access the Indexer instead of the Store"""
    path = urllib.unquote((request.getPathInfo())[1:])
    # replace the above with:
    # path = '/'.join(request.getRequestURL().split('/')[2:])
    # if the snakelet matches an arbitrary pattern
    if path == '':
      path = 'HomePage'
    a = self.getWebApp()
    ac = self.getAppContext()
    ac.indexer.registerHit(path)
    buffer = request.getHeader('If-Modified-Since')
    if buffer != None:
      since = time.mktime(rfc822.parsedate(buffer))
      try:
        # see if our page has been rendered and has a modification time
        our = ac.cache.mtime('soup:' + path)
        if(since > our):
          # Reset some headers
          response.setHeader("Cache-Control",'')
          response.setHeader("Pragma",'')
          response.setHeader("Expires",'')
          # Say bye bye
          response.setResponse(304, "Not Modified")
          return None
      except KeyError:
        pass
    
    # Check for any standing redirects
    redirect = self.checkRedirects(ac,path)
    if redirect:
      response.HTTPredirect(ac.base + redirect)
      return None
      
    # Check for a URL variant
    try:
      page = ac.store.getRevision(path)
    except IOError:
      alias = ac.indexer.resolveAlias(path, True) # go for approximate matches
      if alias != path:
        response.HTTPredirect(ac.base + alias)
        return
      else:
        page = ac.store.getRevision("meta/EmptyPage")
        return (page.headers, renderPage(ac,page,request,response,ac.indexer.done))
    if 'x-redirect' in page.headers.keys():
      uri = page.headers['x-redirect']
      (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
      if schema in self.i18n['uri_schemas'].keys():
        path = uri
      else:
        path = ac.base + path
      response.HTTPredirect(path)
      return
    return (page.headers, renderPage(ac,page,request,response,ac.indexer.done))

  def checkRedirects(self, appcontext, page):
    try:
      redirects = appcontext.redirects
    except:
      return None
    for pattern in redirects.keys():
      redirect = re.sub(pattern,redirects[pattern], page)
      if cmp(redirect,page):
        return redirect
    return None
