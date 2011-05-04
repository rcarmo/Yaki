"""
Python interface to Webthumb API (see http://bluga.net/webthumb/)

By Ross Poulton - www.rossp.org

License: Use this how you like, just don't claim it as your own because
         that isn't cool. I'm not responsible for what this script does.

Modified by Rui Carmo - the.taoofmac.com
"""

import time, cgi, os, httplib, traceback

import xml.dom.minidom
from xml.dom.minidom import Node

WEBTHUMB_HOST='webthumb.bluga.net'
WEBTHUMB_URI='/api.php'

VALID_SIZES = (
    'small',
    'medium',
    'medium2',
    'large',
)

def submit_job(apikey, url):
  request = u"""
  <webthumb>
    <apikey>%s</apikey>
      <request>
        <url>%s</url>
      </request>
  </webthumb>
  """ % (apikey, url)

  try:
    h = httplib.HTTPConnection(WEBTHUMB_HOST)
    h.request("GET", WEBTHUMB_URI, request)
    response = h.getresponse()
    type = response.getheader('Content-Type', 'text/plain')
    body = response.read()
    h.close()
  except:
    print "Webthumb: Error submitting job to server:"
    traceback.print_exc()
    return None
  if type == 'text/xml':
    # This is defined as 'success' by the API. text/plain is failure.
    doc = xml.dom.minidom.parseString(body)
    key = None
    for node in doc.getElementsByTagName("job"):
      wait = node.getAttribute('estimate')
      for node2 in node.childNodes:
        if node2.nodeType == Node.TEXT_NODE:
          key = node2.data
    # We're given an approx time by the webthumb server,
    # we shouldn't request the thumbnail again within this
    # time.
    if key:
      return {'key':key,'wait':wait }
    else:
      return None
  else:
    print "Webthumb: server response was %s" % body
    return None

def get_thumbnail(apikey, key, output_path, size='medium'):
  if size not in VALID_SIZES:
    return False

  request = """
  <webthumb>
    <apikey>%s</apikey>
    <fetch>
      <job>%s</job>
      <size>%s</size>
    </fetch>
  </webthumb>
  """ % (apikey, key, size)

  h = httplib.HTTPConnection(WEBTHUMB_HOST)
  h.request("GET", WEBTHUMB_URI, request)
  response = h.getresponse()
  try:
    os.unlink(output_path)
  except:
    pass
  buffer = response.read()
  print "Webthumb: got file of length %d" % len(buffer)
  h.close()
  if buffer[6:10] == 'JFIF':
    img = file(output_path, "wb")
    img.write(buffer)
    img.close()
    return True
  else:
    print "Webthumb: server response was: %s" % buffer
    return False
