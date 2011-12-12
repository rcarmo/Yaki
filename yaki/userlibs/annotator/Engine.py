#!/usr/bin/env python
# encoding: utf-8
"""
Engine.py

Created by Rui Carmo on 2011-12-12.
Published under the MIT license.
"""

from snakeserver.snakelet import Snakelet
import logging
log=logging.getLogger("Snakelets.logger")

import os, sys, time, rfc822, unittest, urlparse, urllib, re, stat, cgi
import fetch, simplejson, codecs

try:
    import json
except:
    import simplejson as json

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Expose-Headers': 'Location',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
    'Access-Control-Max-Age': '86400'
}

class Engine(Snakelet):
  """
  Basic implementation of Annotator REST API
  based on https://github.com/okfn/annotator-store/blob/master/annotator/store.py
  """

  def getDescription(self):
    return "Annotator API"

  def allowCaching(self):
    return True

  def requiresSession(self):
    return self.SESSION_DONTCREATE

  def serve(self, request, response):
    request.setEncoding("UTF-8")
    response.setEncoding("UTF-8")
    a = request.getWebApp()
    ac = a.getContext()
    c = request.getContext()
    c.fullurl = request.getBaseURL() + request.getFullQueryArgs()

    try:
      route = re.match('^\/(.+)[/]$', request.getPathInfo()[1:])
      return getattr(self,"do_%s" % methodname)(request, response)
    except Exception, e:
      log.debug("Error handling %s" % c.fullurl)
      response.setContentType("application/json")
      response.setHeader("Cache-Control",'max-age=86400')
      response.setHeader("Expires", httpTime(time.time() + 86400))
      response.getOutput().write('[]')
      return

  def do_search(self, request, response):
    c.fullurl = request.getBaseURL() + request.getFullQueryArgs()
    pass

  def do_annotations(self, request, response):
    c.fullurl = request.getBaseURL() + request.getFullQueryArgs()
    pass

