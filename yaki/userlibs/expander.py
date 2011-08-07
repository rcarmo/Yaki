#!/usr/bin/env python
# encoding: utf-8
"""
expander.py

Created by Rui Carmo on 2009-06-22.

Distributed under the MIT License.
"""
import urllib, urllib2, urlparse, httplib, cgi, socket

# BITLY_AUTH = 'login=%s&apiKey=%s' % ('login', 'key')

class URLShortener:
  """ URL shortener class that tries several services until one responds with a shortened URL. """
  services = {
    'tinyurl.com':'/api-create.php?url=',
    'is.gd':'/api.php?longurl=',
    #'api.bit.ly':"http://api.bit.ly/shorten?version=2.0.1&%s&format=text&longUrl=" % BITLY_AUTH,
    'api.tr.im':'/api/trim_simple?url='
  }
  
  def query(self, url):
    for shortener in self.services.keys():
      print shortener
      c = httplib.HTTPConnection(shortener)
      c.request("GET", self.services[shortener] + urllib.quote(url))
      r = c.getresponse()
      shorturl = r.read().strip()
      if ("Error" not in shorturl) and ("http://" + urlparse.urlparse(shortener)[1] in shorturl):
        return shorturl
      else:
        continue
    raise IOError
  

  
class URLExpander:
  """ URL Expander that resolves short URLs recursively until we get a proper URL """
  # known shortening services
  shorteners = ['tr.im','is.gd','tinyurl.com','bit.ly','snipurl.com','cli.gs','feedproxy.google.com','feeds.arstechnica.com']
  twofers = [u'\u272Adf.ws']
  # learned hosts
  learned = []
    
  def resolve(self, url, components):
    """ Try to resolve a single URL """
    c = httplib.HTTPConnection(components.netloc)
    try:
      c.request("GET", components.path, headers={'User-Agent':'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19'})
    except socket.error, e:
      print "URL Expander: Error connecting to resolve %s: %s" % (url, e)
      return url # keep the calling routine happy
    try:
      r = c.getresponse()
    except httplib.BadStatusLine, e:
      print "URL Expander: Error resolving %s: %s" % (url, e)
      return url # keep the calling routine happy
    l = r.getheader('Location')
    if l == None or l == "/":
      return url # it might be impossible to resolve, so best leave it as is
    else:
      return l
  
  def query(self, url, recurse = True):
    """ Resolve a URL """
    components = urlparse.urlparse(url)
    # Check weird shortening services first
    if (components.netloc in self.twofers) and recurse:
      url = self.query(self.resolve(url, components), False)
    # Check known shortening services first
    if components.netloc in self.shorteners:
      url = self.resolve(url, components)
    # If we haven't seen this host before, ping it, just in case
    if components.netloc not in self.learned:
      ping = self.resolve(url, components)
      if ping != url:
        self.shorteners.append(components.netloc)
        self.learned.append(components.netloc)
        url = ping
        
    # Cleanup Feedburner junk
    (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
    query = cgi.parse_qs(query)
    if "utm_source" in query.keys():
      for i in ["utm_source","utm_campaign","utm_medium"]:
        try:
          del query[i]
        except:
          pass
    query = urllib.urlencode(query)
    components = (scheme, netloc, path, params, query, fragment)
    cleaned = urlparse.urlunparse(components)
    return cleaned
  


if __name__ == '__main__':
  e = URLExpander()
  print e.query('http://om.bit.ly/D7bp9')
  print e.query(u'http://\u272Adf.ws/dgw')
  s = URLShortener()
  print s.query('http://www.google.com')
