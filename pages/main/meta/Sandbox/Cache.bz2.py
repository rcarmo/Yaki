#!/usr/bin/env python
# encoding: utf-8
"""
Cache.py

An on-disk cache using SQLite that can fall back on SHA1 hashing, using a dict-like API

Created by Rui Carmo on 2006-08-19.
Redesigned for SQLite on 2009-04-07.
Published under the MIT license.
"""

from __future__ import generators
import os, sys, stat, sha, string, urllib, codecs, time, random

__author__ = ('Rui Carmo http://the.taoofmac.com')
__revision__ = "$Id$"
__version__ = "0.2"
__all__ = ['DiskCache','SQLCache']

try:
  import cPickle as pickle
except ImportError:
  import pickle # fall back on Python version

INTP_VER = sys.version_info[:2]
if INTP_VER < (2, 3):
    raise RuntimeError("Python v.2.3 or later needed")

class HashCache(dict):
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
    return self.stats(key)[0]
  
  def stats(self,key):
    """
    Return os.stats [mtime, size, inode] results on a cache item
    """
    path = self.key2path(key)
    quote = urllib.quote(key,'')
    try:
      stats = os.stat(os.path.join(path,quote))
      return [stats.st_mtime, stats.st_size, stats.st_inode]
    except:
      raise KeyError


class SQLCache(dict):
  def __init__(self, path):
    self.__path = path + '.db'
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    # SQLite is rather loose with keywords, so we can actually use 'key'
    c.execute("create table if not exists cache (key text unique primary key, mtime date, value blob)")
    c.execute("create index if not exists mtime on cache (mtime desc)")
    db.commit()
    dict.__init__(self)    
  
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
    """ Remove from cache any items older than a specified time """
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    c.execute("delete from cache where (mtime < ?)", when)
    self.__db.commit()
    c.close()
    db.close()
      
  def keys(self):
    """ Iterate over the cache contents """
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    c.execute("select key from cache")
    for row in c:
      yield row[0]
    c.close()
    db.close()

  def __setitem__(self,key,val):
    """ Store an item in the cache """
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    val = sqlite3.Binary(pickle.dumps(val).encode('bz2'))
    c.execute("replace into cache (key,mtime,value) values (?,?,?)", (key, time.time(), val))
    db.commit()
    c.close()
    db.close()

  def __delitem__(self,key):
    """ Remove item from cache """
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    # we need to check if it exists to maintain semantics
    c.execute("select from cache where (key = ?)", key)
    if not c.fetchone():
      raise KeyError
    c.execute("delete from cache where (key = ?)", key)
    db.commit()
    c.close()
    db.close()

  def __getitem__(self,key):
    """ Retrieve item from the cache """
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    # we need to check if it exists to maintain semantics
    c.execute("select value from cache where (key = ?) limit 1", (key,))
    try:
      value = pickle.loads(str(c.fetchone()[0]).decode('bz2'))
    except:
      raise KeyError
    c.close()
    db.close()
    return value

  def mtime(self,key):
    """ Return the creation/modification time of a cache item """
    db = sqlite3.connect(self.__path)
    c = db.cursor()
    # we need to check if it exists to maintain semantics
    c.execute("select mtime from cache where key = ? limit 1", (key,))
    try:
      mtime = c.fetchone()[0]
    except:
      raise KeyError
    c.close()
    db.close()
    return mtime

try:
  import sqlite3
  Cache = SQLCache
except ImportError:
  Cache = HashCache

if __name__=="__main__":
  c = Cache('test')
  buffer = ''.join([random.choice(''.join([chr(x) for x in range(ord('a'),ord('z'))])) for x in xrange(4096)])
  t = time.time()
  for i in range(10):
    c[str(i)] = buffer
  print "Took %fs" % (time.time() - t)
  c['foo'] = u'bar'
  print c.mtime('foo')
  print c['foo']
