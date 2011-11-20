#!/usr/bin/env python
# encoding: utf-8
"""
Cache.py

An on-disk cache based on SHA1 hashing with a dict-like API

Created by Rui Carmo on 2006-08-19.
Published under the MIT license.
"""

from __future__ import generators
import os, sys, stat, sha, string, urllib, codecs

__author__ = ('Rui Carmo http://the.taoofmac.com')
__revision__ = "$Id$"
__version__ = "0.1"
__all__ = ['Cache']


try:
  import cPickle as pickle
except ImportError:
  import pickle # fall back on Python version

INTP_VER = sys.version_info[:2]
if INTP_VER < (2, 3):
    raise RuntimeError("Python v.2.3 or later needed")

class Cache(dict):
  def __init__(self, path):
    self.__path = path
    dict.__init__(self)    
  
  def key2path(self,key):
    """
    Generate a disk path out of a key
    """
    raw = sha.new(key)
    digest = raw.hexdigest()
    # Over-the-top hashing
    #steps = [digest[i:i+2] for i in range(0,len(digest),2)]
    # Use 2-level paths
    steps = [digest[i:i+2] for i in range(0,4,2)]
    steps.append(digest[4:])
    return os.path.join(self.__path, string.join(steps,os.path.sep))
  
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
    for folder, subfolders, files in os.walk(self.__path):
      for f in files:
        mtime = os.stat(os.path.join(folder,f))[stat.ST_MTIME]
        if mtime < when:
          os.remove(os.path.join(folder,f))
          os.rmdir(folder)
  
  def keys(self):
    """
    Iterate over the cache contents
    """
    for folder, subfolders, files in os.walk(self.__path):
      for f in files:
        yield urllib.unquote(f)
  
  def __setitem__(self,key,val):
    """
    Store an item in the cache
    """
    path = self.key2path(key)
    quote = urllib.quote(key,'')
    if(not os.path.exists(os.path.join(path,quote))):
      os.makedirs(path)
    open(os.path.join(path,quote),'wb').write(pickle.dumps(val))
    
  def __delitem__(self,key):
    """
    Remove item from cache
    """
    path = self.key2path(key)
    quote = urllib.quote(key,'')
    if os.path.exists(path):
      os.remove(os.path.join(path,quote))
      os.rmdir(path)
    else:
      raise KeyError
  
  def __getitem__(self,key):
    """
    Retrieve item from the cache
    """
    path = self.key2path(key)
    quote = urllib.quote(key,'')
    try:
      return pickle.loads(open(os.path.join(path,quote), "rb").read())
    except:
      raise KeyError
  
  def mtime(self,key):
    """
    Return the creation/modification time of a cache item
    """
    return self.stats(key)[stat.ST_MTIME]
  
  def stats(self,key):
    """
    Return os.stats results on a cache item
    """
    path = self.key2path(key)
    quote = urllib.quote(key,'')
    try:
      return os.stat(os.path.join(path,quote))
    except:
      raise KeyError


if __name__=="__main__":
  c = Cache('../cache')
  c['foo'] = 'bar'
  print c['foo']
  del c['foo']
  c['test/path/name'] = "test"
  for i in c.keys():
    print i
