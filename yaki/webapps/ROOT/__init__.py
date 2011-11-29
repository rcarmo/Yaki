#!/usr/bin/env python
# encoding: utf-8

# standard libraries
import os, codecs, re, socket, Queue
# Snakelets core
from snakeserver.plugin import ErrorpagePlugin
import logging
log = logging.getLogger("Snakelets.logger")

# Yaki libraries
import yaki.Haystack, yaki.Engine, yaki.Feeds, yaki.Indexer, yaki.Tracker, yaki.LinkBlog, yaki.Plugins, yaki.Notifier, yaki.Redirect

# configuration for this webapp
name="Yaki"
defaultRequestEncoding = defaultOutputEncoding = "utf-8"
sessionTimeoutSecs=1800

# for URL generation and basic setup - must match webapps/__init__.py if you're using vhosts, otherwise you'll get mis-formatted URLs
vhost="localhost:9090"

# This is where page templates and themes go
# (path is relative to this file)
docroot="../../../web/main"

# templates for HTML snippets
templates = ['generic', 'simplified', 'journal', 'linkblog', 'linkblog-with-thumbnail', 'linkblog-with-quicklook', 'comments-link', 'comments-enabled', 'comments-soon', 'comments-disabled', 'rss-feed', 'rss-item', 'rss-item-update', 'rss-footer', 'rss-styles', 'error-page', 'json-item']

# Customize site URLs here
siteroot =  "p"     # Wiki root
media =     "m"     # file attachments
journal =   "blog"  # Journal namespace

# Theme -- name must match a folder in 'web/<wiki-name>/themes/'
theme = "bootstrap"

# This is the root or primary wiki, so these are top-level routes for URLs
snakelets = {
  siteroot:     yaki.Engine.Wiki,           # Wiki
  media:        yaki.Engine.Attachment,     # file attachments
  "f":          yaki.Engine.FontPreview,    # font preview generator
  "t":          yaki.Engine.Thumbnail,      # image thumbnails
  "r":          yaki.Feeds.RSS,             # RSS feeds
  "index.sn":   yaki.Redirect.Redirect      # redirect ROOT requests to Wiki
}
defaultErrorPage = "/error.y"

configItems = {
  "services": { # external stuff requiring authentication
  },
  "feedbehavior": { # whether or not to send external links
    '/r': 'x-link'
  },
  # Site info (for meta tags, RSS, etc.)
  # the siteurl is used to build absolute URLs
  "siteinfo": {'sitename': 'Yaki', # RSS feeds
               'sitetitle': 'Yaki', # page titles
               'sitedescription': 'Just another Yaki site',
               'siteurl': 'http://' +  vhost,
               'siteroot': siteroot,
               'theme': theme,
               'media': media,
               'journal': journal
  },
  # match hostnames to deployment settings
  # staging: True disables full text indexing
  "deployment": {
    # page store
    ".+": {"store": "../../../pages/main", "staging": False }
  },
  # Theme
  "theme": "themes/%s" % theme,
  # Locale
  "locale": "en_US",
  # The base URLs for Wiki pages and media, used for URL generation
  "base": "/%s/" % siteroot,
  "media": "/%s/" % media,
  "thumb": "/t/",
  "fontpreview": "/f/",
  # Special page prefixes we use in lieu of namespaces
  "namespaces": ['apps','Hardware','HOWTO','meta','dev','tests','docs',journal,'people','links','podcast','stories'],
  # default author - you really, really want to change this...
  "author": "Administrator",
  # Jabber ID to send notifications to
  "jid": "",
  # default markup - only used if nothing else is specified.
  "defaultmarkup": "text/x-markdown",
  # del.icio.us/Yahoo Pipes feed for linkblog - comment to disable
  # "linkblog": { 'url': "http://feeds.delicious.com/v2/rss/USER/post:links", 'format': 'rss', 'authors': {'USER':'User Name'} },
  # maximum age for HTTP and disk caching
  "maxage": 3600,
  # time frame for enabling comments (blog namespace only, disabled if zero)
  "commentwindow": 15 * 86400,
  # standing redirects for legacy/alternate pathnames
  "redirects" : { # standing redirects - THESE ARE REGULAR EXPRESSIONS AND MATCHED AS SUCH!
    '^p$' : 'start', 
    '^%s\/(\d+)-(\d+)$' % journal : '%s/\\1/\\2' % journal,
    '^%s\/(\d+)-(\d+)-(\d+)$' % journal : '%s/\\1/\\2/\\3' % journal,
    '^%s\/(\d+)-(\d+)-(\d+).(\d+):(\d+)$' % journal : '%s/\\1/\\2/\\3/\\4\\5' % journal
  },
  "dumbagents" : re.compile(".*(Apple-PubSub|YandexBot|GoogleBot|msnbot|bingbot|Mediapartners).*", re.IGNORECASE) # User-agents that should not be redirected to alternative URLs and get 404s
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
  log.info("Initializing webapp %s" % webapp)
  home = os.environ.get("HOME","")
  hashroot = os.path.normpath(os.path.join(webapp.getFileSystemPath(),'..','..','var',name))
  c = webapp.getContext()
  c.name = name
  # Bulk setting of attributes based on config items above
  for i in ['base','commentwindow','defaultmarkup','locale','fontpreview','media','thumb','namespaces','theme','redirects','siteinfo','dumbagents']:
    setattr(c,i,webapp.getConfigItem(i))
  # Haystacks and file caches of various descriptions
  c.cache = yaki.Haystack.Haystack(os.path.join(hashroot,'cache'), basename = "pages")
  #c.cache.enabled = False
  c.gzipcache = yaki.Haystack.Haystack(os.path.join(hashroot,'cache'), basename = "gzip")
  c.persistent = yaki.Haystack.Haystack(os.path.join(hashroot,'persistent'), basename = "stats")
  c.indexstate = yaki.Haystack.Haystack(os.path.join(hashroot,'index'))
  # Templates (taken from the theme directory)
  log.info("%s: init templates" % webapp)
  c.templates = {}
  for t in templates:
    c.templates[t] = unicode(codecs.open(os.path.join(webapp.getFileSystemPath(),docroot,c.theme,'templates','%s.txt' % t),'r','utf-8').read().strip())
  log.info("%s: init page store" % webapp)
  deployment = webapp.getConfigItem('deployment')
  c.staging = False
  for hostname in deployment.keys():
    if re.match(hostname, socket.gethostname()):
      pageroot = os.path.normpath(os.path.join(webapp.getFileSystemPath(), deployment[hostname]['store']))
      c.staging = deployment[hostname]['staging']
      break
  c.store = yaki.Store.Store(pageroot)
  log.info("%s: init wiki plugins" % webapp)
  c.plugins = yaki.Plugins.PluginRegistry(webapp)
  log.info("%s: init linkblog importer" % webapp)
  c.linkblog = yaki.LinkBlog.Importer(webapp)
  c.linkblog.start()
  log.info("%s: init indexing" % webapp)
  if c.staging == True:
    log.info("%s: staging mode. full text indexing is disabled." % webapp)
  c.indexer = yaki.Indexer.Indexer(c, hashroot + '/index', c.store, c.cache, c.staging)
  c.indexer.start()
  log.info("%s: ready." % webapp)

def close(webapp):
  log.info("%s: shutting down..." % webapp)
  c = webapp.getContext()
  c.indexer.stop()
  log.info("%s: stopped." % webapp)

