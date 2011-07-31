#!/usr/bin/env python
# encoding: utf-8

# standard libraries
import os, codecs, re, socket, Queue
# Snakelets core
from snakeserver.plugin import ErrorpagePlugin
# Yaki libraries
import yaki.Haystack, yaki.Engine, yaki.Feeds, yaki.Indexer, yaki.Tracker, yaki.LinkBlog, yaki.Plugins, yaki.Notifier

# configuration for this webapp
name="Yaki Secondary Wiki"
vhost="localhost"
docroot="web"
defaultRequestEncoding = defaultOutputEncoding = "utf-8"
sessionTimeoutSecs=1800
templates = ['generic', 'simplified', 'journal', 'linkblog', 'linkblog-with-thumbnail', 'linkblog-with-quicklook', 'comments-link', 'comments-enabled', 'comments-soon', 'comments-disabled', 'rss-feed', 'rss-item', 'rss-item-update', 'rss-footer', 'rss-styles', 'error-page', 'json-item']
snakelets= {
  "space"    : yaki.Engine.Wiki,       # The main Wiki snakelet
  "media"    : yaki.Engine.Attachment, # The file attachment server
  "thumbnail": yaki.Engine.Thumbnail,  # The thumbnail server
  "sponsored": yaki.Feeds.RSS,         # The RSS snakelet
  "json-data": yaki.Feeds.JSON,        # The JSON snakelet
  "track"    : yaki.Tracker.Referrals  # Referral Tracker (uses client-side JavaScript)
}
defaultErrorPage = "/error.y"

configItems = {
  "services": { # external stuff requiring authentication
  },
  "feedbehavior": { # whether or not to send external links
    '/sponsored': 'x-link'
  },
  # The site info (for meta tags, RSS, etc.)
  # the siteurl is used to build absolute URLs
  "siteinfo": {'sitename': 'Yaki', # RSS feeds
               'sitetitle': 'Yaki', # page titles
               'sitedescription': 'Just another Yaki site',
               'siteurl': 'http://' +  vhost,
               'ping' : {'technorati':'http://' + vhost}
  },
  # Machine names and local pathnames for deployment.
  # staging: True disables full text indexing
  # store: None defaults to ~yaki/space
  "deployment": {
    "dummy": {"store": "/home/user/space", "staging": False }
  },
  # Theme
  "theme": "themes/minimal",
  # Locale
  "locale": "en_US",
  # The base URLs for Wiki pages and media, used for URL generation
  "base": "/space/",
  "media": "/media/",
  # Special page prefixes we use in lieu of namespaces
  "namespaces": ['apps','Hardware','HOWTO','meta','dev','tests','docs','blog','people','links','podcast','stories'],
  # default author - you really, really want to change this...
  "author": "Administrator",
  # Jabber ID to send notifications to
  "jid": "",
  # default markup - only used if nothing else is specified.
  "defaultmarkup": "text/x-textile",
  # del.icio.us/Yahoo Pipes feed for linkblog - comment to disable
  #"linkblog": { 'url': "http://feeds.delicious.com/v2/rss//post:links", 'format': 'rss', 'authors': {'rcarmo':'Rui Carmo'} },
  # maximum age for HTTP and disk caching
  "maxage": 3600,
  # time frame for enabling comments (blog namespace only, disabled if zero)
  "commentwindow": 15 * 86400,
  # standing redirects for legacy/alternate pathnames
  "redirects" : { # standing redirects
    'space' : 'HomePage', 
    '^blog\/(\d+)-(\d+)$' : 'blog/\\1/\\2',
    '^blog\/(\d+)-(\d+)-(\d+)$' : 'blog/\\1/\\2/\\3',
    '^blog\/(\d+)-(\d+)-(\d+).(\d+):(\d+)$' : 'blog/\\1/\\2/\\3/\\4\\5'
  },
}

class YakiErrorpagePlugin(ErrorpagePlugin):
  PLUGIN_NAME="YakiErrorpage"
  def setTemplate(self, hostname, template):
    self.hostname = hostname
    self.template = template
  def plug_serverErrorpage(self, path, code, message, explanation, outputStream):
    hostname = self.hostname
    meta = ''
    heading = 'Ouch!'
    outputStream.write(self.template % vars())
    return True

def init(webapp):
  print ">> INIT WEBAPP",webapp
  home = os.environ.get("HOME","")
  c = webapp.getContext()
  # Bulk setting of attributes based on config items above
  for i in ['base','commentwindow','defaultmarkup','locale','media','namespaces','theme','redirects','siteinfo']:
    setattr(c,i,webapp.getConfigItem(i))
  # Haystacks and file caches of various descriptions
  cachefolder = os.path.join(webapp.getFileSystemPath(),'../../var/cache')
  indexfolder = os.path.join(webapp.getFileSystemPath(),'../../var/index')
  c.cache = yaki.Haystack.Haystack(cachefolder, basename = "pages")
  c.gzipcache = yaki.Haystack.Haystack(cachefolder, basename = "gzip")
  c.persistent = yaki.Haystack.Haystack(cachefolder, basename = "persistent")
  c.indexstate = yaki.Haystack.Haystack(indexfolder, basename = "state")
  # Templates (taken from the theme directory)
  print ">> INITIALIZING TEMPLATES", webapp
  c.templates = {}
  for t in templates:
    c.templates[t] = unicode(codecs.open(os.path.join(webapp.getFileSystemPath(),docroot,c.theme,'templates','%s.txt' % t),'r','utf-8').read().strip())
  print ">> INITIALIZING STORE", webapp
  deployment = webapp.getConfigItem('deployment')
  root = os.path.join(webapp.getFileSystemPath(),'..','..','content','space2')
  print "INFO: using %s as document root" % root
  c.staging = False
  for hostname in deployment.keys():
    if re.match("^%s" % hostname, socket.gethostname()):
      root = deployment[hostname]['store']
      c.staging = deployment[hostname]['staging']
  c.store = yaki.Store.Store(root)
  print "INFO: %s:%s" % (hostname,root)
  print ">> INITIALIZING YAKI PLUGINS", webapp
  c.plugins = yaki.Plugins.PluginRegistry(webapp)
  try:
    auth = webapp.getConfigItem('services')['xmpp']
    c.notifier = yaki.Notifier.XMPPNotifier(auth['username'], auth['password'])
  except:
    pass
  #auth = webapp.getConfigItem('services')['twitter']
  #c.twitter = yaki.Notifier.TwitterNotifier(auth['key'], auth['secret'], os.path.join(webapp.getFileSystemPath(),'tokens','twitter.token'), os.path.join(os.path.expanduser("~"),'var','db','tweets.db'))
  #print ">> INITIALIZING LINKBLOG IMPORTER", webapp
  #c.linkblog = yaki.LinkBlog.Importer(webapp)
  #c.linkblog.start()
  print ">> INITIALIZING INDEX", webapp
  if c.staging == True:
    print "INFO: Staging mode. full text indexing is disabled."
  c.indexer = yaki.Indexer.Indexer(c, indexfolder, c.store, c.cache, c.staging)
  c.indexer.start()
  print ">> DONE INIT WEBAPP", webapp

def close(webapp):
  print ">> CLOSE WEBAPP",webapp
  c = webapp.getContext()
  c.indexer.stop()
  c.notifier.disconnect()
  print ">> DONE CLOSE WEBAPP",webapp
