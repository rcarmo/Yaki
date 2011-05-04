#!/usr/bin/env python
# encoding: utf-8
"""
fetch.py - URL helper

Created by Rui Carmo on 2005-03-19, based on original code by Mark Pilgrim.

Published under the MIT license.
"""
__version__ = "0.3"

import httplib, urlparse, urllib2, gzip, re, Queue
from datetime import date
import htmllib
import formatter
from StringIO import StringIO

# Spoof IE for most news sites
USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)"

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
  def http_error_301(self, req, fp, code, msg, headers):
    result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
    result.status = code
    return result 

  def http_error_302(self, req, fp, code, msg, headers):
    result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
    result.status = code
    return result 

class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler): 
  def http_error_default(self, req, fp, code, msg, headers):
    result = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp) 
    result.status = code
    return result 

def openURL(source, etag=None, lastmodified=None, agent=USER_AGENT):
  httplib.HTTPConnection.debuglevel = 0
  if hasattr(source, 'read'):
    return source
  if source == '-':
    return sys.stdin
  # non-HTTP code removed for brevity
  if urlparse.urlparse(source)[0] == 'http':
    request = urllib2.Request(source)
    request.add_header('User-Agent', agent)
    if etag:
      request.add_header('If-None-Match', etag)
    if lastmodified:
      request.add_header('If-Modified-Since', lastmodified)
    request.add_header('Accept-encoding', 'gzip')
    opener = urllib2.build_opener(SmartRedirectHandler(), DefaultErrorHandler())
    return opener.open(request)
  try:
    return open(source)
  except(IOError,OSError):
    pass
  return StringIO(str(source))

def fetchURL(source, etag=None, lastmodified=None, agent=USER_AGENT):
  result = {}
  f = openURL(source, etag, lastmodified, agent)
  result['data'] = f.read()
  if hasattr(f, 'headers'):
    result['etag'] = f.headers.get('ETag')
    result['lastmodified'] = f.headers.get('Last-Modified')
    if f.headers.get('content-encoding', '') == 'gzip':
      result['data'] = gzip.GzipFile(fileobj=StringIO(result['data'])).read()
  if hasattr(f, 'url'):
    result['url'] = f.url
    result['status'] = 200
  if hasattr(f, 'status'):
    result['status'] = f.status
  f.close()
  return result
