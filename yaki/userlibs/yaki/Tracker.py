#!/usr/bin/env python
# encoding: utf-8
"""
Tracker.py

'Clean' referrer tracking using JavaScript.

Created by Rui Carmo on 2007-03-21.
Published under the MIT license.
"""
from snakeserver.snakelet import Snakelet
import os, sys, time, rfc822, unittest, urlparse, urllib, re, hashlib
from yaki.Utils import *
import yaki.Locale

# List of referrals to ignore
# (web aggregators, search engines, etc. that tend to cause too many hits)
ignorelist = ["^localhost", "^(127|10|192\.168)\.+","^taoofmac.com",
# Portuguese search engines
"^pesquisa",
# French search engines
"^recherche",
# Personalized homepages
"^(www.netvibes.com)",
# Webmail
"mail.yahoo.com",
"hotmail.com",
# Social Networks
"web.pond.pt", "(www\.)facebook.com", "dabr.co.uk",
# Other search engines
"^(tw.search.yahoo.com|aolsearch|uk.ask.com|www.ask.com|ask.com|blogs.icerocket.com)", "^(\w+)\.google\.", 
"^(search.creativecommons.org|search.naver|search.msn|search.live|a9.com|www.metacrawler.com)",
"^(www.bloglines.com|bloglines.com|www.newsgator.com)",
"^(findory.com|www.dogpile.com|www.answers.com|swik.net)"]

# List of referrals from which query strings should be pruned
prunelist = ['^(del.icio.us|delicious.com)']

class Referrals(Snakelet):
  """
  Referral Tracker
  """
  
  def init(self):
    s = self.getContext()
    ac = self.getAppContext()    
    ac.refkeys = {}
    ac.referrers = ReferrerCache(ac,ignorelist,prunelist)
    self.mtime = time.time()
  
  def getDescription(self):
    return "Referral Tracker"

  def allowCaching(self):
    return False
    
  def requiresSession(self):
    return self.SESSION_NOT_NEEDED
  
  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    now = time.time()
    # pattern is /track/action/key/url
    s = self.getContext()
    a = request.getWebApp()
    ac = a.getContext()
    referrer = request.getReferer()
    # store a checkpoint of referrer information at the cache's leisure
    ac.referrers.commit()
    #if(preg_match(SITE_REGEXP, $_SERVER["HTTP_REFERER"])) {
    try:
      (dummy,action,key,url) = request.getFullQueryArgs().split('/',3)
      url = urllib.unquote(url)
    except:
      response.setResponse(404, "Not Found")
      return
    # invoked from <script type="text/javascript" src="/track/key"></script>
    if action == "key":
      # current time, up to the second - good enough for most purposes
      now = time.time()
      # create new entry
      refkey = hashlib.sha1(str(now) + referrer).hexdigest()
      # store the key, the time and the local site page we were called from
      (schema,host,path,parameters,query,fragment) = urlparse.urlparse(referrer)
      ac.refkeys[refkey] = (now,path[len(ac.base):])
      # wipe out anything older than 30 seconds
      wiped = []
      for i in ac.refkeys.keys():
        (then,referrer) = ac.refkeys[i]
        if (now - 30) > then:
          wiped.append(i)
      for i in wiped:
        try:
          del ac.refkeys[i] 
        except:
          pass
      response.setHeader("Content-Type",'text/plain')
      response.getOutput().write('"%s"' % refkey)
      return
    elif action == "do":
      # split referrer URL 
      (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(url)
      for i in ignorelist:
        if re.match(i,netloc):
          schema = 'skip'
      # Only track URLs with valid keys and schemas
      if re.match('^[a-f0-9]{40}$',key) and schema in ['http','https']:
        # If we know this key
        if key in ac.refkeys.keys():
          (now,page) = ac.refkeys[key]
          # Check if this is an internal referrer - we may have a siteurl override parameter
          try:
            (schema,host,path,parameters,query,fragment) = urlparse.urlparse(ac.siteinfo['siteurl'])
          except:
            (schema,host,path,parameters,query,fragment) = urlparse.urlparse(request.getBaseURL())
          if host != netloc:
            ac.referrers.add(url,page,now)
      # Keep the remote browser happy
      self.getWebApp().serveStaticFile(self.getWebApp().getDocRootPath() + "/img/1x1t.gif", response, useResponseHeaders=False)
      return
    response.setResponse(404, "Not Found")
  
class ReferrerCache:
  def __init__(self, ac, ignorelist = [], prunelist = []):
    self.ac = ac
    self.ignorelist = ignorelist
    self.prunelist = prunelist
    self.mtime = time.time()
    self.data = None
    self.getData()
  
  def commit(self):
    now = time.time()
    if (self.mtime + 300) < now:
      self.ac.persistent['tracker:referrers'] = self.data
      self.ac.persistent.commit()

  def getData(self):
    if self.data is None:
      try:
        self.data = self.ac.persistent['tracker:referrers']
      except:
        self.data = {}    
    return self.data
    
  def add(self, referrer, page, now):
    referrer = referrer.strip()
    page = urllib.unquote(page.strip())
    self.getData()
    if(referrer == '' or page == ''):
      return
    (schema,host,path,parameters,query,fragment) = urlparse.urlparse(referrer)
    for i in self.ignorelist:
      if re.match(i, host):
        return
        
    for i in self.prunelist:
      if re.match(i, host):
        referrer = schema + "://" + host + path
    
    if page in self.data.keys():
      if referrer in self.data[page]['referrers']:
        self.data[page]['referrers'][referrer]['count'] = self.data[page]['referrers'][referrer]['count'] + 1
        self.data[page]['referrers'][referrer]['mtime'] = now
      else:
        self.data[page]['referrers'][referrer] = {'count':1, 'mtime':now}
      self.data[page]['mtime'] = now
    else:
      self.data[page] = {'mtime': now,'referrers': {referrer:{'count':1, 'mtime':now}}}

    try:
      for page in self.data.keys():
        if self.data[page]['mtime'] < (now - 3600*24):
          del self.data[page]
        for referrer in self.data[page]['referrers']:
          if self.data[page]['referrers'][referrer]['mtime'] < (now - 3600*24):
            del self.data[page]['referrers'][referrer]
          if len(self.data[page]['referrers']) == 0:
            del self.data[page]
    except KeyError:
      pass
    self.mtime = now
