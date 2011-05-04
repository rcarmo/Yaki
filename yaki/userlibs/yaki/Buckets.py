#!/usr/bin/env python
# encoding: utf-8
"""
Buckets.py

Created by Rui Carmo on 2009-02-28.
Published under the MIT license.
"""

import time
try:
  import json
except:
  import simplejson as json

class TimedBucket:
  """
  Store measurements over time slots with automatic expiration of older samples
  """
  
  def __init__(self, granularity, expiration):
    self.granularity = granularity
    self.expiration  = expiration
    self.buckets = {}
    self.start = time.time()

  def addToBucket(self, value = 1):
    now = time.time()
    # use integer division to force rounding
    currslot = int(now) / self.granularity * self.granularity
    if currslot in self.buckets.keys():
      self.buckets[currslot] = self.buckets[currslot] + value
    else:
      self.buckets[currslot] = value
    try:
      del self.buckets[currslot - self.expiration]
    except:
      pass
      
  def getBuckets(self):
    return self.buckets

  def getJSON(self):
    return json.dumps(self.buckets)
    
if __name__ == '__main__':
  a = TimedBucket(5, 15)
  for x in range(120):
    a.addToBucket(1)
    print a.getBuckets()
    time.sleep(2)
