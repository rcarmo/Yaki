#!/usr/bin/env python
# encoding: utf-8
"""
Utils.py

Miscellaneous utility functions

Created by Rui Carmo on 2006-09-10.
Published under the MIT license.
"""

import math, time, datetime, calendar, unittest, feedparser
import os, sys, re, binascii, fnmatch, xmlrpclib, cgi, htmlentitydefs
import yaki.Locale

#
# Shared data - constants, definitions, etc.
# 

# Characters used for generating page/URL aliases
ALIASING_CHARS = ['','.','-','_']

# Prefixes used to identify attachments (cid is MIME-inspired)
ATTACHMENT_SCHEMAS = ['cid','attach']

# regexp for matching caching headers
MAX_AGE_REGEX = re.compile('max-age(\s*)=(\s*)(\d+)')

# regexp for sanitizing titles
SANITIZE_TITLE_REGEX = re.compile('^(blog|links)')

#
# Date handling
#

# Embrace and extend Mark's feedparser mechanism
_textmate_date_re = \
    re.compile('(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$')

def parseDate(date):
  """
  Parse a TextMate date (YYYY-MM-DD HH:MM:SS, no time zone, assume it's always localtime)
  """
  m = _textmate_date_re.match(date)
  if not m:
    return time.mktime(feedparser._parse_date(date))
  return time.mktime(time.localtime(calendar.timegm(time.gmtime(time.mktime(time.strptime(date,"%Y-%m-%d %H:%M:%S"))))))

def isoTime(value=None):
  """
  Time string in ISO format
  """
  if value == None:
    value = time.localtime()
  tz = time.timezone/3600
  return time.strftime("%Y-%m-%dT%H:%M:%S-", value) + ("%(tz)02d:00" % vars())

def httpTime(value=None):
  """
  Time string for HTTP headers
  """
  if value == None:
    value = time.time()
  return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(value))

def plainDate(i18n,date):
  """
  Format a date consistently
  """
  if isinstance(date, float) or isinstance(date, int):
    date = time.localtime(date)
  # trickery to replace leading zero in month day
  mday    = time.strftime(" %d",date).replace(" 0"," ").strip()
  weekday = i18n[time.strftime("%A",date)]
  month   = i18n[time.strftime("%B", date)]
  year    = time.strftime("%Y", date)
  # build English ordinal suffixes
  day = int(mday)
  if day > 20:
    day = int(mday[1])
  try:
    suffix = ['th','st','nd','rd'][day]
  except:
    suffix = 'th'
  return i18n['journal_date_format'] % locals()
  
  
def fuzzyTime(i18n, date=None):
  intervals = {
    '00:00-00:59': 'latenight',
    '01:00-03:59': 'weehours',
    '04:00-06:59': 'dawn',
    '07:00-08:59': 'breakfast',
    '09:00-12:29': 'morning',
    '12:30-14:29': 'lunchtime',
    '14:30-16:59': 'afternoon',
    '17:00-17:29': 'teatime',
    '17:30-18:59': 'lateafternoon',
    '19:00-20:29': 'evening',
    '20:30-21:29': 'dinnertime',
    '21:30-22:29': 'night',
    '22:30-23:59': 'latenight'  
  }
  if isinstance(date, float) or isinstance(date, int):
    date = time.localtime(date)
  then = time.strftime("%H:%M",date)
  for i in intervals.keys():
    (l,u) = i.split('-')
    # cheesy (but perfectly usable) string comparison
    if l <= then and then <= u:
      return i18n[intervals[i]]
  return None

def plainTime(i18n, value=None, addtime=False):
  """
  A simple time string
  """
  value = float(value)
  if addtime:
    format = ", %H:%M"
  else:
    format = ''
  if time.localtime(value)[0] != time.localtime()[0]:
    # we have a different year
    format = " %Y" + format
  format = i18n[time.strftime("%b",time.localtime(value))] + " %d" + format
  return time.strftime(format, time.localtime(value)).strip()

def timeSince(i18n, older=None,newer=None,detail=2):
  """
  Human-readable time strings, based on Natalie Downe's code from
  http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
  Assumes time parameters are in seconds
  """
  intervals = {
    31556926: 'year', # corrected from the initial 31536000
    2592000: 'month',
    604800: 'week',
    86400: 'day',
    3600: 'hour',
    60: 'minute',
  }
  chunks = intervals.keys()
  
  # Reverse sort using a lambda (for Python 2.3 backwards compatibility)
  chunks.sort(lambda x, y: y-x)
  
  if newer == None:
    newer = time.time()
  
  interval = newer - older
  if interval < 0:
    return i18n['some_time']
    # We should ideally do this:
    # raise ValueError('Time interval cannot be negative')
    # but it makes sense to fail gracefully here
  if interval < 60:
    return i18n['less_1min']
  
  output = ''
  for steps in range(detail):
    for seconds in chunks:
      count = math.floor(interval/seconds)
      unit = intervals[seconds]
      if count != 0:
        break
    if count > 1:
      unit = unit + 's'
    if count != 0:
      output = output + "%d %s, " % (count, i18n[unit])
    interval = interval - (count * seconds)
  output = output[:-2]
  return output
  
#
# String utility functions
#

def rsplit(s, sep=None, maxsplit=-1):
  """
  Equivalent to str.split, except splitting from the right.
  """
  if sys.version_info < (2, 4, 0):
    if sep is not None:
      sep = sep[::-1]
    L = s[::-1].split(sep, maxsplit)
    L.reverse()
    return [s[::-1] for s in L]
  else:
    return s.rsplit(sep, maxsplit)


def shrink(line,bound=50,rep='[...]'):
  """
  Shrinks a string, adding an ellipsis to the middle
  """
  l = len(line)
  if l < bound:
    return line
  if bound <= len(rep):
    return rep
  k = bound - len(rep)
  return line[0:k/2] + rep + line[-k/2:]

def convertentity(m):
  if m.group(1)=='#':
    try:
      return unichr(int(m.group(2)))
    except ValueError:
      return '&#%s;' % m.group(2)
  try:
    return unichr(htmlentitydefs.name2codepoint[m.group(2)])
  except KeyError:
    return '&%s;' % m.group(2)

def converthtml(s):
  return re.sub(r'&(#?)(.+?);',convertentity,s)

#
# File utility functions
#

def locate(pattern, root=os.getcwd()):
  """
  Generator for iterating inside a file tree
  """
  for path, dirs, files in os.walk(root):
    for filename in [os.path.abspath(os.path.join(path, filename)) for filename in files if fnmatch.fnmatch(filename, pattern)]:
      yield filename

#
# Wild Wild Web
#

def hasComments(ac, path):
  override = "off"
  if re.match('^blog', path):
    override = "on"
  # check if this node has comments explicitly enabled or disabled
  try:
    override = ac.indexer.pageinfo[path]['x-comments'].lower()
  except:
    pass
  if override in ['on','enabled','yes']:
    return True
  elif override in ['off','disabled','no']:
    return False
  return False

def formatComments(ac, request, path, journal = False):
  c = request.getContext()
  # Try to use the main site URL to avoid trouble with reverse proxying and port numbers
  try:
    siteurl = ac.siteinfo['siteurl'] 
  except:
    siteurl = request.getBaseURL()
  baseurl = siteurl + ac.base
  c.comments = ""
  
  # check if we need to deal with comments here
  if hasComments(ac,path) and ac.commentwindow > 0:
    try:
      mtime = ac.indexer.pageinfo[path]['last-modified']
      title = ac.indexer.pageinfo[path]['title']
      permalink = baseurl + path
      rawlink = permalink.replace("http://","")
      window = mtime + ac.commentwindow - time.time()
      context = {'page':path, 'window': str(int(window/86400)), 'permalink': permalink, 'rawlink': rawlink, 'title': cgi.escape(title)}
      if int(window/86400) > 0:
        if journal:
           c.comments = ac.templates['comments-link'] % context
        else:
           c.comments = ac.templates['comments-enabled'] % context
      else:
        c.comments = ac.templates['comments-disabled'] % context
    except:
      c.comments = ac.templates['comments-soon']
      pass

def sanitizeTitle(title):
  return re.sub("[\W+]","-",title.lower())

def doPings(siteinfo):
  try:
    for target in siteinfo['ping']:
      if target == 'technorati':
        print "Pinging Technorati..."
        server = xmlrpclib.Server('http://rpc.technorati.com/rpc/ping')
        print server.weblogUpdates.ping(siteinfo['sitetitle'], siteinfo['ping'][target])
  except:
    pass

def makeUnique(seq, transform=None):  
  # order preserving 
  if transform is None: 
    def transform(x): return x 
  seen = {} 
  result = [] 
  for item in seq: 
    marker = transform(item) 
    if marker not in seen:
      seen[marker] = 1
      result.append(item)
  return result


if __name__ == "__main__":
  import Locale
  print plainTime(Locale.i18n["en_US"],parseDate("2010-04-18 08:09:00"), True)
