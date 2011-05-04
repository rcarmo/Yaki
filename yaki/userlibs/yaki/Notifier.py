#!/usr/bin/env python
# encoding: utf-8
"""
Notifier.py

A set of notifier classes

Created by Rui Carmo on 2009-08-04.
Published under the MIT license.
"""

import os, xmpp, expander, twitter, sqlite3, pickle

try: 
  import json
except:
  import simplejson as json

class XMPPNotifier:
  def __init__(self,username,password):
    self.username = username
    self.password = password
    self.queue = []
    self.connect()

  def connect(self):
    print ">> INITIALIZING XMPP"
    self.jid = xmpp.protocol.JID(self.username)
    self.cl=xmpp.Client(self.jid.getDomain(),debug=[])
    print "XMPP connect..."
    self.con=self.cl.connect()
    if not self.con:
      print "XMPP: could not connect!"
    print "XMPP: connected with %s" % self.con
    self.auth = self.cl.auth(self.jid.getNode(),self.password,resource=self.jid.getResource())
    if not self.auth:
      print "XMPP: could not authenticate!"
    self.cl.sendInitPresence(requestRoster=0)
    print "DONE INIT XMPP"

  def disconnect(self):
    print "XMPP STOP"
    self.cl.disconnect()

  def send(self, jid, message):
    if self.auth:
       try:
         id=self.cl.send(xmpp.protocol.Message(jid,message))
         print 'XMPP to %s: %s' % (jid, message)
       except IOError:
         print 'ERROR: XMPP CONNECTION FAILED, LOST NOTIFICATION to %s: %s' % (jid, message)
         self.connect()
       except:
         print 'ERROR: FAILED XMPP to %s: %s' % (jid, message)

class TwitterNotifier:
  def __init__(self, key, secret, token, db):
    self.key = key
    self.secret = secret
    self.token = token
    self.db = db
    if not os.path.exists(self.token):
      api = twitter.OAuthApi(key, secret)
      request_token = api.getRequestToken()
      print api.getAuthorizationURL(request_token)
      api = twitter.OAuthApi(key, secret, request_token)
      access_token = api.getAccessToken(raw_input("Please enter the PIN: "))
      open(self.token,'w').write(pickle.dumps(access_token))
    else:
      access_token=pickle.loads(open(self.token,'r').read())
    self.api = twitter.OAuthApi(key, secret, access_token)
    self.user = self.api.getUserInfo()
    db = sqlite3.connect(self.db)
    c = db.cursor()
    c.execute('create table if not exists tweets (url text, status text)')
    c.execute('create unique index if not exists url on tweets (url asc)')
    db.commit()
    c.close()
    self.shortener = expander.URLShortener()
  
  def send(self, url, title, link = True, trim = 120):
    db = sqlite3.connect(self.db)
    c = db.cursor()
    ellipsis = u'\u2026'
    separator = u' '
    marker = u'\u262F '
    c.execute("select * from tweets where url=?",(str(url),))
    if c.rowcount > 0:
      return # do not re-tweet links
    shorturl = self.shortener.query(url)
    if link:
      if len(title) > (trim + len(separator) + len(shorturl)):
        shortened = title[0:trim - len(ellipsis) - len(separator) - len(shorturl)] + ellipsis + separator + shorturl
      else:
        shortened = title + separator + shorturl
    else:
      if len(title) > (trim + len(marker) + len(separator) + len(shorturl)):
        shortened = marker + title[0:trim - len(marker) - len(ellipsis) - len(separator) - len(shorturl)] + ellipsis + separator + shorturl
      else:
        shortened = marker + title + separator + shorturl
    print "Tweeting %s" % shortened, len(shortened)
    status = self.api.PostUpdate(shortened)
    #print "posted %s and got %s" % (shortened, status)
    c.execute("insert or ignore into tweets (url, status) values (?,?)", (url, shortened))
    db.commit()
    c.close()
