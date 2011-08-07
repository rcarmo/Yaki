#!/usr/bin/env python
# encoding: utf-8
"""
Attachments.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from yaki.Utils import *
from BeautifulSoup import *
import re, urlparse, cgi

try:
  import cPickle as pickle
except ImportError:
  import pickle # fall back on Python version

class AttachmentsWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
    self.schemas = self.i18n['uri_schemas']
    registry.register('markup',self, 'plugin','Attachments')

  def run(self, serial, tag, tagname, pagename, soup, request, response):  
    headers = {}
    try:
      headers = pickle.loads(self.ac.cache['headers:'+pagename].encode('utf-8'))
    except:
      pass
    if 'x-attachments' in headers.keys():
      attachments = [name.strip() for name in headers['x-attachments'].split(',')]
      buffer = '<ul>'
      for i in attachments:
        buffer = buffer + '<li><a href="cid:%s">%s</a></li>' % (i,i)
      buffer = buffer + '</ul>'
      tag.replaceWith(BeautifulSoup(buffer))
      return
    tag.replaceWith('')
  
class AttachedImagesWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
    self.schemas = self.i18n['uri_schemas']
    registry.register('markup',self, 'img','attachedimages')

  def run(self, serial, tag, tagname, pagename, soup, request, response):
    try:
      uri = tag['src']
    except KeyError:
      return True

    # Try to handle the uri as a schema/path pair
    (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
    
    if schema.lower() in ATTACHMENT_SCHEMAS or self.ac.store.isAttachment(pagename, path):
      tag['src'] = unicode(cgi.escape(self.ac.media + pagename + "/" + path))
      # No further processing is required
      return False
    return True
      

class LinkToAttachmentsWikiPlugin(yaki.Plugins.WikiPlugin):
    def __init__(self, registry, webapp):
      self.ac = webapp.getContext()
      self.i18n = yaki.Locale.i18n[self.ac.locale]
      self.schemas = self.i18n['uri_schemas']
      #registry.register('markup',self, 'a','attachedfiles')

    def run(self, serial, tag, tagname, pagename, soup, request, response):
      try:
        uri = tag['href']
      except KeyError:
        return True

      print "INFO: %s, %s" % (pagename, uri)

      # Try to handle the uri as a schema/path pair
      (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)

      if schema.lower() in ATTACHMENT_SCHEMAS or self.ac.store.isAttachment(pagename, path):
        tag['href'] = unicode(self.ac.media + pagename + "/" + path)
        tag['title'] = self.schemas['attach']['title'] % {'uri':os.path.basename(uri)}
        tag['class'] = self.schemas['attach']['class']
        # No further processing is required
        return False
      return True
