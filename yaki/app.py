#! /usr/bin/env python

import snakeserver.server
import os, sys, time, hashlib
import getopt # we're not going to use argparse to maintain pre-2.7 compatibility

# ---enable this to see possible memory leaks---
#import gc
#gc.set_debug(gc.DEBUG_LEAK)

def usage():
  print """Usage: %s [--debug][--bind=<ip>][--port=<num>][--external-port=<num>][--workdir=<path>]""" % sys.argv[1]

def main():
  HTTPD_PORT = 9090
  HTTPD_IP = '127.0.0.1'
  HTTPD_EXTERNAL_PORT = 9090
  RUNAS_USER = None # "www"
  RUNAS_GROUP = None # "www"
  WORKDIR = None
  DEBUG = False

  try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["debug", "workdir=", "bind=", "port=", "external-port="])
  except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)
  output = None
  verbose = False
  for o, a in opts:
    if o in ("-b", "--bind"):
      HTTPD_IP = a
    elif o in ("-p", "--port"):
      HTTPD_PORT = int(a)
    elif o in ("-e", "--external-port"):
      HTTPD_EXTERNAL_PORT = int(a)
    elif o in ("-w", "--workdir"):
      WORKDIR = a
    elif o in ("-d", "--debug"):
      DEBUG = True
    else:
      assert False, "unhandled option"

  if WORKDIR:
    os.chdir(WORKDIR)

  print >>sys.stderr,"%s GMT Starting server on %s:%d (%d)" % (time.asctime(time.gmtime()), HTTPD_IP, HTTPD_PORT, HTTPD_EXTERNAL_PORT)

  # TODO: move more of these to getopt above
  snakeserver.server.main(
    HTTPD_PORT=HTTPD_PORT,
    bindname=HTTPD_IP,
    externalPort=HTTPD_EXTERNAL_PORT,
    serverURLprefix='',
    debugRequests=DEBUG,
    precompileYPages=True,
    writePageSource=False,
    serverRootDir=None,
    runAsUser=RUNAS_USER,
    runAsGroup=RUNAS_GROUP,
    escrow = hashlib.sha1(str(time.time)).hexdigest()
  )

if __name__=="__main__":
  main()
