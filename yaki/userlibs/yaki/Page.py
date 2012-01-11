#!/usr/bin/env python
# encoding: utf-8
"""
Page.py

Created by Rui Carmo on 2006-08-19.
Published under the MIT license.
"""

# ============================================================================
# Wiki Page
# ============================================================================

import rfc822

# Allow module to load regardless of textile or markdown support
try:
  import textile
  import markdown
except ImportError:
  pass

# helper functions for rendering

def _markdown(buffer):
  return markdown.Markdown(extensions=['extra','toc'], safe_mode=False).convert(buffer)

def _plaintext(buffer):
  return u'<pre>\n%s</pre>' % buffer

def _textile(buffer):
  # this one is necessary due to textile's use of kargs
  return textile.textile(unicode(buffer), head_offset=0, sanitize=1, encoding='utf-8', output='utf-8')

def _html(buffer):
  return buffer


class Page:
  """
  Wiki Page - handles storage format and markup
  """
  
  def __init__(self, buffer, mimetype='text/plain'):
    """
    Constructor
    """
    self.mimetype = mimetype
    self.headers = {}
    self.raw = ''
  
    if mimetype in ['text/plain', 'text/x-textile', 'text/x-markdown']:
      try:
        (header_lines,self.raw) = buffer.split("\n\n", 1)
        for header in header_lines.strip().split("\n"):
          # Allow for comments in headers
          if header.strip()[0] == '#':
            continue
          (name, value) = header.strip().split(":", 1)
          self.headers[name.lower().strip()] = unicode(value.strip())
      except:
        raise TypeError, "Invalid page file format."
     # TODO: parse HTML using lxml or similar to read headers from meta tags
     # ...and consider adding the option to grab EXIF data from a JPEG file for 
     # a photoblog
  
  def rfc2822(self):
    """
    Render this page into an RFC2822 buffer
    """
    buffer = ''
    for header in self.headers.keys():
      buffer = buffer + header + ": " + self.headers[header] + "\n"
    buffer = buffer + "\n\n" + self.raw
    return buffer
  
  # TODO: change order of parameters (it's inconsistent with constructor)
  def update(self, markup, text):
    self.raw = text
    self.headers['content-type'] = markup
  
  def render(self, default = 'text/x-textile'):
    """
    Render page contents as HTML
    """
    try:
      format = self.headers['content-type']
    except:
      format = default
    #print "Format: %s, %s" % (format, self.headers['title'])
    self.html = {u'text/plain': _plaintext,
                 u'text/x-web-markdown': _markdown,
                 u'text/x-markdown': _markdown,
                 u'text/markdown': _markdown,
                 u'text/textile': _textile,
                 u'text/x-textile': _textile,
                 u'text/html': _html}[format](unicode(self.raw))
    return self.html

