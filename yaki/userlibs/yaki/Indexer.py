#!/usr/bin/env python
# encoding: utf-8
"""
Indexer.py

Created by Rui Carmo on 2007-02-19.
Published under the MIT license.
"""

import os, errno, time, gc, difflib
import threading, urlparse
from BeautifulSoup import *
from yaki.Engine import renderPage
from yaki.Buckets import TimedBucket
from yaki.Utils import *
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.analysis import StemmingAnalyzer, KeywordAnalyzer
from whoosh.qparser import QueryParser
from whoosh.writing import BatchWriter

class Indexer(threading.Thread):

  def __init__(self, appcontext, path, store, cache, staging):
    """
    Setup environment
    """
    threading.Thread.__init__(self)
    self.path = path
    try:
      os.makedirs(self.path)
    except OSError, e: # it already exists
      if e.errno == errno.EEXIST:
        pass
    self.staging = staging
    c = self.appcontext = appcontext
    self.ready = False
    self.allpages = {}
    self.done = False
    c.indexstate['started'] = time.time()
    try:
      self.hitmap = c.persistent['indexer:hitmap']
    except:
      self.hitmap = TimedBucket(3600,3600*24*7) # hit map for page statistics

    try: # to restore previously indexed data upon startup
      self.pageinfo         = c.indexstate['indexer:pageinfo']
      self.backlinks        = c.indexstate['indexer:backlinks']
      self.wikilinks        = c.indexstate['indexer:wikilinks']
      self.interwikilinks   = c.indexstate['indexer:interwikilinks']
      self.outboundlinks    = c.indexstate['indexer:outboundlinks']
      self.defaultlinks     = c.indexstate['indexer:defaultlinks']
      self.wantedlinks      = c.indexstate['indexer:wantedlinks']
      self.indexed          = c.indexstate['indexer:indexed']
      self.tags             = c.indexstate['indexer:tags']
      # build the 'recent' helper array
      self.recent  = [name for name in self.pageinfo.keys()]
      self.recent.sort(lambda x, y: cmp(self.pageinfo[y]['last-modified'],self.pageinfo[x]['last-modified']))
      self.done = True
      print "Indexer: state restored."
    except: # go at it from scratch
      print "Indexer: state reset."
      self.pageinfo       = {} # all page headers
      self.backlinks      = {} # all backlinks across pages
      self.wikilinks      = {} # all wikilinks across pages
      self.interwikilinks = {} # all interwikilinks
      self.outboundlinks  = {} # all http and https links
      self.defaultlinks   = {} # default links associated with specific pages
      self.wantedlinks    = {} # all missing pages and where
      self.tags           = {} # all tags
      self.recent = []    # recently modified pages
      self.indexed = {}   # page name and time of last indexing
      self.deleted = []   # deleted pages since last pass
      self.indexable = [] # all pages, sorted by on-disk modification date
    self.aliases = {}     # page aliases
    self.working = True
    self.whoosh = None
    self.schema = Schema(name=ID(stored=True,unique=True),
                         title=TEXT(stored=True,analyzer=StemmingAnalyzer()),
                         body=TEXT(stored=True,analyzer=StemmingAnalyzer()),
                         wiki=KEYWORD(lowercase=True, commas=True),
                         link=KEYWORD(commas=True),
                         date=TEXT(stored=True),
                         modified=TEXT(stored=True),
                         tags=KEYWORD(stored=True,lowercase=True, commas=True))
  
  def stop(self):
    self.working = False
  
  def run(self):
    self.pagescan() # Do preliminary scanning
    gc.collect() # make sure we release memory
    # Wait for 5s before starting full-text indexing
    for i in range(0, 5):
      time.sleep(1)
      if not self.working:
        return
    # Play nice and allow for thread to be killed externally with minimum delay
    while(self.fullscan()):
      for i in range(0, 360):
        time.sleep(5)
        if not self.working:
          return
  
  def fullscan(self):
    """Full text index of content"""
    if self.staging:
      return
    print "Indexer: Scanning pages"
    self.pagescan()
    print "Indexer: Rebuilding"
    c = self.appcontext
    # Check if a previous fulltext index already exists
    try:
      self.whoosh = index.open_dir(self.path)
      print "Indexer: Opening existing index"
    except:
      self.whoosh = index.create_in(self.path, self.schema)
      self.indexed = {}      
      print "Indexer: Creating new index"
    self.writer = BatchWriter(self.whoosh)
    
    if len(self.deleted):
      dirty = True
    else:
      dirty = False
    count = 1
    bound = len(self.indexable)
    
    for name in self.deleted:
      self.whoosh.delete_by_term('name',name)
      print "Indexer: deleting %s" % name
      try:
        del self.indexed[name]
      except:
        pass
      try:
        del self.pageinfo[name]
      except:
        pass
      
    # Go through all pages, starting with most recently modified files on disk
    for name in self.indexable:
      if self.working == False:
        self.writer.commit()
        return False

      print "Indexer: indexing %s" % name
      try:
        dummy = self.backlinks[name]
      except:
        self.backlinks[name] = []

      try:
        dummy = self.wikilinks[name]
      except:
        self.wikilinks[name] = []
      
      try:
        # was the page modified on disk since we last saw it?
        if c.store.mtime(name) != self.indexed[name]:
          raise KeyError
        else:
          headers = self.pageinfo[name]
          continue
      except KeyError:
        # Get the page
        start = time.time()
        try:
          page = c.store.getRevision(name)
        except:
          print u'Indexer: ERROR: Could not index %s, will be re-visited upon next indexing pass.' % name
          count = count + 1
          continue
        
        # Cache the header info
        self.pageinfo[name] = headers = page.headers
                
        # If pages have an "x-link" header then keep track of it
        if "x-link" in headers:
          self.defaultlinks[name] = page.headers['x-link']
          outboundlinks = [page.headers['x-link']]
        else:
          outboundlinks = []
        
        # If pages are non-indexable just flag them as indexed and continue the loop
        if "x-index" in headers:
          if page.headers["x-index"].lower() == "no":
            self.indexed[name] = c.store.mtime(name)
            count = count + 1
            continue

        wikilinks = []
        buckets = []
        # Start building inter-page links by resolving tags
        parse = ['keywords', 'categories', 'tags'] # headers to parse
        for header in parse:
          if header in page.headers:
            tags = [tag.strip().lower() for tag in headers[header].split(',')]
            for tag in tags:
              if tag not in buckets:
                buckets.append(tag)
              if not tag in self.tags.keys():
                self.tags[tag] = []
              if not name in self.tags[tag]:
                self.tags[tag].append(name)
              if tag in self.aliases.keys():
                wikilinks.append(self.aliases[tag])
        
        # Grab the page HTML
        soup = BeautifulSoup(renderPage(self.appcontext, page, cache=False, indexing=True))

        # Identify and store all wikilinks in markup
        links = soup.findAll('a', {'class':'wiki'})
        for link in links:
          (schema, netloc, path, parameters, query, fragment) = urlparse.urlparse(link['href'])
          path = path[len(self.appcontext.base):]
          path = self.resolveAlias(path)
          if not path in wikilinks:
            wikilinks.append(path)
        self.wikilinks[name] = wikilinks

        # Identify and store all outbound links in markup
        links = soup.findAll('a', {'class':re.compile('^(http|https|ftp)')})
        for link in links:
          href = link['href']
          if not href in outboundlinks:
            outboundlinks.append(href)
         
        # Identify and store all interwiki links
        links = soup.findAll('a', {'class':'interwiki'})
        for link in links:
          href = link['href']
          if not href in outboundlinks:
            outboundlinks.append(href)
          rel = link['rel']
          (schema, netloc, path, parameters, query, fragment) = urlparse.urlparse(rel)
          schema = schema.lower()
          if not schema in self.interwikilinks:
            self.interwikilinks[schema] = {}
          if not path in self.interwikilinks[schema]:
            # store the first title and mtime we come across, since we're assuming the indexer
            # will always index newer pages first
            self.interwikilinks[schema][path] = {'mtime': c.store.mtime(name), 'href': link['href'], 'title':link['title'], 'text': u''.join(link.findAll(text=re.compile('.+'))).strip(), 'pages':[name]}
          else:
            if name not in self.interwikilinks[schema][path]['pages']:
              self.interwikilinks[schema][path]['pages'].append(name)

        # These will be _all_ the outbound links, including interwiki links
        self.outboundlinks[name] = outboundlinks
          
        # Identify and store all unknown wiki links
        self.wantedlinks[name] = []
        links = soup.findAll('a',{'class':'wikiunknown'})
        for link in links:
          (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(link['href'])
          path = path[len(self.appcontext.base):]
          if path not in self.wantedlinks[name]:
            self.wantedlinks[name].append(path)
        
        # Gather together all plaintext and remove some extra whitespace
        plaintext = u' '.join(soup.findAll(text=re.compile('.+')))
        for p in [u'.',u',',u':',u'-',u' ']:
          plaintext=plaintext.replace(u' ' + p,p)
        
        # Perform backlinks update across pages
        for href in self.wikilinks[name]:
          if href not in self.backlinks:
            self.backlinks[href] = []
          if name not in self.backlinks[href]:
            self.backlinks[href].append(name)
        
        # Index the plaintext
        self.index(soup, page.headers, name, plaintext, self.wikilinks[name], self.outboundlinks[name])
        dirty = True
        print "Indexer: %s done (%d of %d): %fs" % (name, count, bound, time.time()-start)
        if not (count % 100):      
          self.snapshot(c)
        count = count + 1
        self.indexed[name] = c.store.mtime(name)
    if dirty:
      print "Indexer: Saving context"
      self.snapshot(c)
      print "Indexer: Sorting recent pages"
      self.recent  = [name for name in self.pageinfo.keys()]
      self.recent.sort(lambda x, y: cmp(self.pageinfo[y]['last-modified'],self.pageinfo[x]['last-modified']))
      print "Indexer: Closing index"
      self.writer.commit()
      print "Indexer: Indexing complete"
    else:
      # save the hitmap and pageinfo at regular intervals
      c.indexstate['indexer:pageinfo'] = self.pageinfo
      c.indexstate.commit()
      c.persistent['indexer:hitmap'] = self.hitmap
      c.persistent.commit()
      self.writer.commit()
      print "Indexer: No updates performed"  
    print "Indexer: Freeing RAM"
    gc.collect()
    self.done = True
    return True
    
  def snapshot(self,c):
    c.persistent['indexer:hitmap'] = self.hitmap
    c.persistent.commit()
    c.indexstate['indexer:backlinks'] = self.backlinks
    c.indexstate['indexer:wikilinks'] = self.wikilinks
    c.indexstate['indexer:interwikilinks'] = self.interwikilinks
    c.indexstate['indexer:outboundlinks'] = self.outboundlinks
    c.indexstate['indexer:defaultlinks'] = self.defaultlinks
    c.indexstate['indexer:pageinfo'] = self.pageinfo
    c.indexstate['indexer:wantedlinks'] = self.wantedlinks
    c.indexstate['indexer:indexed'] = self.indexed
    c.indexstate['indexer:tags'] = self.tags
    c.indexstate.commit()
  
  def pagescan(self):
    """Perform a shallow page scan"""
    c = self.appcontext
    self.allpages = c.store.allPages()
    self.aliases = c.store.aliases
    print "Indexer: Total pages: %d" % len(self.allpages.keys())
    self.deleted = [x for x in self.indexed.keys() if c.store.mtime(x) is None]
    print "Indexer: Deleted pages: %d" % len(self.deleted)
    modified = [x for x in self.indexed.keys() if c.store.mtime(x) > self.indexed[x]]
    print "Indexer: Modified pages: %d" % len(modified)
    indexable = [x for x in self.allpages.keys() if x not in self.indexed.keys()]
    indexable.extend(modified)
    self.indexable = makeUnique(indexable)
    print "Indexer: Indexable pages: %d" % len(self.indexable)
    self.indexable.sort(lambda x, y: self.allpages[y]-self.allpages[x])
    self.ready = True    
  
  def registerHit(self, page):
    self.hitmap.addToBucket()
    try:
      self.pageinfo[page]['x-hit-count'] = self.pageinfo[page]['x-hit-count'] + 1
      self.pageinfo[page]['x-last-hit'] = time.time()
    except:
      try:
        self.pageinfo[page]['x-hit-count'] = 1
        self.pageinfo[page]['x-last-hit'] = time.time()
      except:
        # page may not have been indexed in any form yet
        pass

  def index(self, soup, headers, name, plaintext, wikilinks, outboundlinks):
    """Index a single page"""
    
    # Find title, allowing for legacy entries without one
    titletext = unicode(name)
    if 'title' in headers.keys():
      titletext = headers['title']
    else:
      try:
        # search for initial header (if any)
        title = soup.findAll('h1')[0]
        titletext = u''.join(title.findAll(text=re.compile('.+')))
      except:
        pass
  
    # now add all wikilinks as keywords
    wikilinks = u','.join(wikilinks)
    links = u','.join(outboundlinks)
    
    # and map tags, keywords and categories
    tags = []
    for i in ['tags','keywords','categories']:
      if i in headers.keys():
        for t in headers[i].strip().split(','):
          t = t.strip().lower()
          if t != '':
            tags.append(t)
    tags = u','.join(tags)
    self.writer.update_document(name=unicode(name), 
      title=titletext,
      date=unicode(time.strftime("%Y%m%d%H%M%S",time.localtime(headers['date']))),
      modified=unicode(time.strftime("%Y%m%d%H%M%S",time.localtime(headers['last-modified']))),
      tags=tags,
      wiki=wikilinks, 
      link=links,
      body=titletext + u' ' + plaintext)

  def search(self, query, limit=10, field='body'):
    """Query the index"""
    if not self.done or not self.whoosh:
      return None
    s = self.whoosh.searcher()
    qp = QueryParser(field, schema=self.schema)
    q = qp.parse(query)
    return s.search(q,limit=limit)#,sortedby="modified",reverse="true")
    
  def resolveAlias(self,path,approximate = False):
    """Resolve page aliases - placed here to allow for future re-use of indexing data"""
    # Try finding aliases based on single character manipulation first (dashes, etc.)
    for replacement in ALIASING_CHARS:
      alias = path.lower().replace(' ',replacement)
      if alias in self.aliases.keys():
        return self.aliases[alias]
    # look for similar aliases 
    if approximate:
      similar = difflib.get_close_matches(path,self.aliases.keys())
      if len(similar) > 0:
        similar.sort()
        return self.aliases[similar[0]]
    return path
