#!/usr/bin/env python
# encoding: utf-8
"""
BaseURI.py

A Yaki plugin to reformat links and page references

Created by Rui Carmo on 2006-09-12.
Published under the MIT license.
"""

import yaki.Engine, yaki.Locale
import urlparse, re
from BeautifulSoup import *
from yaki.Utils import *

class BaseURIWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'a','baseuri')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
    self.schemas = self.i18n['uri_schemas']
    
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    try:
      uri = tag['href']
    except KeyError:
      return True
    
    # Try to handle the uri as a schema/path pair
    (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
    known = False
    if schema == '':
      uri = self.ac.indexer.resolveAlias(path)
      if uri != path:
        path = tag['href'] = uri
      if uri in self.ac.indexer.allpages:
        known = True
    
    if(schema == ''):
      if self.ac.store.isAttachment(pagename, path):
        tag['href'] = unicode(self.ac.media + pagename + "/" + path)
        tag['title'] = self.schemas['attach']['title'] % {'uri':os.path.basename(path)}
        tag['class'] = self.schemas['attach']['class']
        return False

      if(known): # this is a known Wiki link, so there is no need to run it through more plugins
        if request is False:
          # check for a direct outbound link
          if path in self.ac.indexer.defaultlinks:
            uri = self.ac.indexer.defaultlinks[path]
            (schema,netloc,path,parameters,query,fragment) = urlparse.urlparse(uri)
            tag['href'] = uri
            tag['title'] = self.schemas[schema]['title'] % {'uri':uri}
            tag['class'] = self.schemas[schema]['class']
            return False
        tag['href'] = self.ac.base + tag['href']
        tag['class'] = "wiki"
        try: # to use indexed metadata to annotate links
          last = self.ac.indexer.pageinfo[path]['last-modified']
          tag['title'] = self.i18n['link_update_format'] % (path,timeSince(self.i18n,last))
        except:
          tag['title'] = self.i18n['link_defined_notindexed_format'] % path
      elif((schema == netloc == path == parameters == query == '') and (fragment != '')):
        # this is an anchor, leave it alone
        tag['href'] = self.ac.base + pagename + "#" + fragment
        tag['class'] = "anchor"
        try:
          exists = tag['title']
        except:
          tag['title'] = self.i18n['link_anchor_format'] % fragment
      else:
        if request is False:
          # remove unknown wiki links for RSS feeds
          tag.replaceWith(tag.contents[0])
          # format for online viewing
        else:
          tag['href'] = self.ac.base + tag['href']
          tag['class'] = "wikiunknown"
          tag['title'] = self.i18n['link_undefined_format'] % path
    elif(schema in self.schemas.keys()): # this is an external link, so reformat it
      tag['title'] = self.schemas[schema]['title'] % {'uri':uri}
      tag['class'] = self.schemas[schema]['class']
      #tag['target'] = '_blank'
    else: # assume this is an interwiki link (i.e., it seems to have a custom schema)
      tag['title'] =  self.i18n['link_interwiki_format'] % uri
      tag['class'] = "interwiki"
      #tag['target'] = '_blank'
      # Signal that this tag needs further processing
      return True
    # We're done
    return False
