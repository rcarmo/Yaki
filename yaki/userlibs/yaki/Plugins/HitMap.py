#!/usr/bin/env python
# encoding: utf-8
"""
HitMap.py

Created by Rui Carmo on 2009-01-09.
Published under the MIT license.
"""

import yaki.Engine, yaki.Store, yaki.Locale
from yaki.Utils import *
import time
from pygooglechart import ScatterChart
from pygooglechart import Axis

class HitMapWikiPlugin(yaki.Plugins.WikiPlugin):
  """
  Generate hitmap using Google Chart API
  """
  def __init__(self, registry, webapp):
    registry.register('markup',self, 'plugin','hitmap')
    self.ac = webapp.getContext()
    self.i18n = yaki.Locale.i18n[self.ac.locale]
    self.data = {}
  
  def run(self, serial, tag, tagname, pagename, soup, request, response):
    width = 384
    height = 512
    buckets = self.ac.indexer.hitmap.getBuckets()
    # transpose data (we might be doing sampling at a different interval, and 
    # here we want weekday:hour slots)
    self.data = {}
    for t in buckets.keys():
      slot = time.strftime("%2w%2H", time.localtime(int(t)))
      if slot in self.data.keys():
        self.data[slot] = self.data[slot] + buckets[t]
      else:
        self.data[slot] = buckets[t]
    grid = {'x':[0 for x in range(6)], 'y':[0 for y in range(23)]}
    x = []
    y = []
    z = []
    buffer = []
    for slot in self.data.keys():
      x.append(1 + int(slot[0:2]))
      y.append(24 - int(slot[2:4]))
      z.append(int(self.data[slot]))
    chart = ScatterChart(width, height, x_range=(0, 7), y_range=(0, 25))
    chart.add_data(x)
    chart.add_data(y)
    chart.add_data(z)
    chart.set_axis_labels(Axis.LEFT, [''] + ["%02dh" % (23 - x) for x in range(24)] + [''])
    chart.set_axis_labels(Axis.TOP, ['', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
    chart.add_marker(0, 1.0, 'o', '00e0e040', 50)
    buffer.append('<img alt="Google Scatter Chart" src="%s">' % chart.get_url())
    tag.replaceWith(u''.join(buffer))
