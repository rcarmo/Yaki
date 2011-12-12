#!/usr/bin/env python
# encoding: utf-8

# standard libraries
import os, codecs, re, socket, Queue

# Snakelets core
import logging
log = logging.getLogger("Snakelets.logger")

# Yaki libraries
import yaki.Haystack

import annotator.Engine

# configuration for this webapp
name="Annotator"
defaultRequestEncoding = defaultOutputEncoding = "utf-8"
sessionTimeoutSecs=1800

# for URL generation and basic setup - must match webapps/__init__.py if you're using vhosts, otherwise you'll get mis-formatted URLs
vhost="localhost"

# This is where page templates and themes go
# (path is relative to this file)
docroot="../../../web/secondary"

# templates for HTML snippets

# This is the root or primary wiki, so these are top-level routes for URLs
snakelets= {
  "api": annotator.Engine.Handler
}

def init(webapp):
  log.info("Initializing webapp %s" % webapp)
  home = os.environ.get("HOME","")
  hashroot = os.path.normpath(os.path.join(webapp.getFileSystemPath(),'..','..','var',name))
  c = webapp.getContext()
  c.name = name
  # Haystacks and file caches of various descriptions
  c.persistent = yaki.Haystack.Haystack(os.path.join(hashroot,'persistent'), basename = "annotations")

def close(webapp):
  log.info("%s: shutting down..." % webapp)
  c = webapp.getContext()
  c.indexer.stop()
  log.info("%s: stopped." % webapp)
