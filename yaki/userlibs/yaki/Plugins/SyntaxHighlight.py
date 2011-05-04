#!/usr/bin/env python
# encoding: utf-8
"""
SyntaxHighlight.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
import urlparse, re, cgi, os
from BeautifulSoup import *
from pygments import highlight
from pygments.lexers import *
from pygments.formatters import *

class SyntaxHighlightWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'pre','syntax')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    try:
      source = tag['src']
      (schema,host,path,parameters,query,fragment) = urlparse.urlparse(source)
      if schema == 'cid' or self.ac.store.isAttachment(pagename,path):
        filename = self.ac.store.getAttachmentFilename(pagename,path)
        if os.path.exists(filename):
          buffer = codecs.open(filename,'r','utf-8').read().strip()
        else:
          tag.replaceWith(self.i18n['error_include_file'])
          return False
      else:
        tag.replaceWith(self.i18n['error_reference_format'])
        return False
    except KeyError:
      buffer = u''.join(tag.findAll(text=re.compile('.+'))).strip()
      #buffer = unicode(BeautifulStoneSoup(buffer,convertEntities=BeautifulStoneSoup.XHTML_ENTITIES)).strip()
    try:
      lexer = tag['syntax']
    except KeyError:
      lexer = 'text'
    if request is False: # we're formatting for RSS
      lexer = 'text'
    lexer = get_lexer_by_name(lexer)
    formatter = HtmlFormatter(linenos=False, cssclass='syntax')
    result = highlight(buffer, lexer, formatter)
    tag.replaceWith(result.strip())
    return False
  
