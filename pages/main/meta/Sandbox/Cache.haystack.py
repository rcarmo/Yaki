#!/usr/bin/env python
# encoding: utf-8
"""
Haystack.py

An on-disk cache based on SHA1 hashing with a dict-like API, inspired by Facebook's Haystack store

Created by Rui Carmo on 2010-04-05
Published under the MIT license.
"""

from __future__ import generators
import os, sys, stat, string, urllib, codecs, time

__author__ = ('Rui Carmo http://the.taoofmac.com')
__revision__ = "$Id$"
__version__ = "0.1"
__all__ = ['Cache']


try:
  import cPickle as pickle
except ImportError:
  import pickle # fall back on Python version

import logging
log=logging.getLogger("Snakelets.logger")

INTP_VER = sys.version_info[:2]
if INTP_VER < (2, 3):
    raise RuntimeError("Python v.2.3 or later needed")

class Cache(dict):
  def __init__(self, path, flush = 300, timeout = 48 * 3600):
    self.__mtime = time.time()
    self.__flushinterval = flush
    self.__timeout = timeout
    self.__path = path
    self.__build
    self.__basename = "haystack"
    self.__build()
    dict.__init__(self)    
  
  def __build(self):
    try:
      os.makedirs(self.__path)
    except:
      pass
    try:
      self.__cache = open(os.path.join(self.__path,self.__basename + '.bin'), "rb+")
    except:
      self.__cache = open(os.path.join(self.__path,self.__basename + '.bin'), "ab+")
    try:
      self.__index = pickle.loads(open(os.path.join(self.__path,self.__basename + '.idx'), "rb").read())
    except:
      self.__index = {} # "key": [mtime,length,offset]
    self.__start = self.__mtime = time.time()
  
  def __flush(self, immediate = False):
    now = time.time()
    if immediate or (now > (self.__mtime + self.__flushinterval)):
      idx = open(os.path.join(self.__path,self.__basename + '.idx'),'wb').write(pickle.dumps(self.__index))
      self.__cache.flush()
      os.fsync(self.__cache)
      self.__mtime = now
    elif (self.__timeout > 0) and (now > (self.__start + self.__timeout)):
      os.unlink(os.path.join(self.__path,self.__basename + '.bin'))
      os.unlink(os.path.join(self.__path,self.__basename + '.idx'))
      self.__build()

  def __eq__(self, other):
    raise TypeError('Equality undefined for this kind of dictionary')
  
  def __ne__(self, other):
    raise TypeError('Equality undefined for this kind of dictionary')
  
  def __lt__(self, other):
    raise TypeError('Comparison undefined for this kind of dictionary')
  
  def __le__(self, other):
    raise TypeError('Comparison undefined for this kind of dictionary')
  
  def __gt__(self, other):
    raise TypeError('Comparison undefined for this kind of dictionary')
  
  def __ge__(self, other):
    raise TypeError('Comparison undefined for this kind of dictionary')
  
  def __repr__(self, other):
    raise TypeError('Comparison undefined for this kind of dictionary')
  
  def expire(self,when):
    """
    Remove from cache any items older than a specified time
    """
    for k in self.__index.keys():
      if self.__index[k][0] < when:
        del self.__index[k]
  
  def keys(self):
    """
    Iterate over the cache contents
    """
    for k in self.__index.keys():
      yield k
      
  def stats(self,key):
    log.debug("Haystack stats request: %s" % key)
    try:
      stats = self.__index[key]
      log.debug("Haystack stats response: %s", stats)
      return stats
    except KeyError:
      log.debug("Haystack key not found for stats request: %s" % key)
      raise KeyError
  
  def __setitem__(self,key,val):
    """
    Store an item in the cache
    Errors will cause the entire cache to be rebuilt
    """
    log.debug("Haystack storing: %s" % key)
    try:
      val = pickle.dumps(val)
      self.__cache.seek(0,os.SEEK_END)
      offset = self.__cache.tell()
      length = len(val)
      self.__cache.write(val)
      mtime = time.time()
      self.__index[key] = [mtime,length,offset]
      self.__flush(True)
      log.debug("Haystack stored: %s, %f, %d, %d" % (key, mtime, length, offset))
    except:
      self.__build()
    
  def __delitem__(self,key):
    """
    Remove item from cache
    In this case, we only remove it from the index
    """
    try:
      del self.__index[key]
    except:
      raise KeyError
    self.__flush()
  
  def __getitem__(self,key):
    """
    Retrieve item from the cache
    """
    try:
      self.__cache.seek(self.__index[key][2])
      return pickle.loads(self.__cache.read(self.__index[key][1]))
    except:
      log.debug("Haystack key not found: %s" % key)
      raise KeyError
  
  def mtime(self,key):
    """
    Return the creation/modification time of a cache item
    """
    try:
      log.debug("Haystack key mtime: %s, %f" % (key, self.__index[key][0]))
      return self.__index[key][0]
    except:
      log.debug("Haystack key mtime not found: %s" % key)
      raise KeyError

if __name__=="__main__":
  c = Cache('.')
  for i in range(1,10000000):
    c['foo'] = 'bar'
    print c['foo']
    del c['foo']
    c['test/path/name'] = "test"
    for i in c.keys():
      print i

