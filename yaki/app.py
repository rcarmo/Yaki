#! /usr/bin/env python

import snakeserver.server
import os, sys, time, hashlib

HTTPD_PORT = 9090
RUNAS_USER = None # "www"
RUNAS_GROUP = None # "www"

# ---enable this to see possible memory leaks---
#import gc
#gc.set_debug(gc.DEBUG_LEAK)

def main(workingdir=None):

  if workingdir:
    os.chdir(workingdir)

  print >>sys.stderr,"%s GMT: serv.py is starting the snakelet server on port %d" % (time.asctime(time.gmtime()), HTTPD_PORT)

  snakeserver.server.main(
    HTTPD_PORT=HTTPD_PORT,
    bindname='127.0.0.1',
    externalPort=80,
    serverURLprefix='',
    debugRequests=False,
    precompileYPages=True,
    writePageSource=False,
    serverRootDir=None,
    runAsUser=RUNAS_USER,
    runAsGroup=RUNAS_GROUP,
    escrow = hashlib.sha1(str(time.time)).hexdigest()
  )

if __name__=="__main__":
  main()

