#!/usr/bin/env python
# encoding: utf-8
"""
TOC.py

Created by Rui Carmo on 2007-01-11.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store
from BeautifulSoup import *
import re, hashlib

class TOCWikiPlugin(yaki.Plugins.WikiPlugin):
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','toc')
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    anchors = {}
    order = []
    for header in range(1,4):
      for htag in soup('h' + str(header)):
        # headers may have other tags
        text = ''.join(htag.findAll(text=re.compile('.+')))
        anchor = text.lower()
        anchor = anchor.replace(' ','-')
        while anchor in anchors:
          anchor = anchor + '-'
        order.append(anchor)
        anchors[anchor] = {'level':header, 'text':text}
        htag.insert(0,'<a name="%s">' % anchor)
        htag.insert(len(htag),'</a>')

    level = 1 
    id = hashlib.sha1(''.join(order)).hexdigest()
    buffer = '<a name="toc"></a><div class="toc"><div class="tocheader" onclick="$(\'%s\').style.display = \'inline\';"><img src="/img/icons/application_view_list.png" align="absmiddle">&nbsp;Contents</div><div id="%s" class="toclisting">' % (id,id)
    for anchor in order:
      if anchors[anchor]['level'] > level:
        for i in range(0,anchors[anchor]['level'] - level):
          if i > 0:
            buffer = buffer + '<li class="toc">'
          buffer = buffer + '<ul class="toc">'
      elif anchors[anchor]['level'] < level:
        buffer = buffer + '</li>'
        for i in range(0,level - anchors[anchor]['level']):
          buffer = buffer + '</ul></li>'
      else:
        buffer = buffer + '</li>'
      level = anchors[anchor]['level']
      buffer = buffer + '<li><a href="%s#%s">%s</a>' % (pagename,anchor,anchors[anchor]['text'])
    for i in range(0, level):
      buffer = buffer + '</li></ul>'
    buffer = buffer + '<img align="right" onclick="$(\'%s\').style.display= \'none\';" src="/img/icons/control_eject.png"></div></div>' % id
    tag.replaceWith(buffer)
    return True
