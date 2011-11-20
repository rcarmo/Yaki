#! /usr/bin/env python

#
# Snakelet Server monitoring script. (designed for Linux;
# works almost 100% on Mac OS X too, even though it lacks pgrep.
#
# Designed to be run from a crontab.
#
# It pings the snakelet server and restarts it in daemon mode
# if it is not responding anymore. (first kills hanging pids)
#
# Dependencies: /usr/sbin/lsof, and pgrep must be available.
#

# -------------- CONFIGURE BELOW: ------------------------
SERVER_HOST = '127.0.0.1'
SERVER_DIR = "/home/user/site/yaki"
LOG_DIR = "/home/user/var/logs"
# -------------- CONFIGURE ENDS --------------------------


import os, socket, time, pwd
import daemon
import sys,traceback


import serv

if not os.path.isdir(SERVER_DIR):
  raise SystemExit("invalid server directory: "+SERVER_DIR)

SERVER_LOG = os.path.join(LOG_DIR, "dev-server.log")
SERVER_ERR_LOG = os.path.join(LOG_DIR, "dev-server_err.log")
SERVER_PID = os.path.join(LOG_DIR, "dev-server.pid")


class ServerDownError(Exception): pass


def tryConnect( host, port ):
  try:
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(30)        # max. 10 seconds
    s.connect( (host,port) )
    s.send("PING / HTTP/1.0\r\n\r\n") 
    reply=s.recv(15)   # just enough for "HTTP/1.1 202 OK"
    if reply.startswith("HTTP/") and (" 200 " in reply or " 202 " in reply):
      return # all is okay
    raise ServerDownError("invalid response to PING method")
  except socket.gaierror,x:
    print "HOST NAME PROBLEM",x
    raise
  except socket.error,x:
    raise ServerDownError(str(x))

def checkServer(force=False, restart=True):
    try:    
      if force:
        raise ServerDownError("(re)start or shutdown forced!")
      print time.asctime(time.localtime()),"checking Snakelets server. Trying to PING to %s:%d ..." %(SERVER_HOST, serv.HTTPD_PORT),
      tryConnect(SERVER_HOST, serv.HTTPD_PORT)
      print "Server is alive."
    except ServerDownError,x:
      print "Server down: ",x
      print "Killing server"
      try:
        daemon.startstop(stdout=SERVER_LOG, stderr=SERVER_ERR_LOG, pidfile=SERVER_PID, action='stop')
      except daemon.DaemonizeError,x:
        print "Ignoring error: ",x

      checkIfPortIsFree(serv.HTTPD_PORT)

      if restart:
        print "Restarting... workdir=",SERVER_DIR
        os.chdir(SERVER_DIR)
        daemon.startstop(stdout=SERVER_LOG, stderr=SERVER_ERR_LOG, pidfile=SERVER_PID, action='start')
        print "%s GMT: This is the daemon." % time.asctime(time.gmtime())
        try:
          serv.main(workingdir=SERVER_DIR)
        except:
          print >>sys.stderr,"\n**** ERROR OCCURRED IN SERVER! (%s GMT) ****" % time.asctime()
          traceback.print_exc(sys.stderr)
          print >>sys.stderr,"**** END OF ERROR, EXITING! ****\n"
          print "%s GMT: an error occured, see the error log!" % time.asctime(time.gmtime())
        print "%s GMT: Daemon ends." % time.asctime(time.gmtime())

def killPids(pids):
  from signal import SIGINT,SIGTERM,SIGKILL
  for pid in pids:
    try:
      pid=int(pid)
      print "PID %d uses port!" % pid
      if pid==os.getpid():
        print "That's us."
        continue
      try:
        while 1:
          print "sending SIGINT to",pid
          os.kill(pid,SIGINT)
          time.sleep(2)
          print "sending SIGTERM to",pid
          os.kill(pid,SIGTERM)
          time.sleep(2)
          print "sending SIGKILL to",pid
          os.kill(pid,SIGKILL)
          time.sleep(1)
      except OSError, err:
        pass # process died, hopefully
    except ValueError:
      pass

def checkIfPortIsFree(HTTPD_PORT):
  print "Checking if port %d is in use..." % HTTPD_PORT
  import commands
  pids= commands.getoutput("/usr/bin/lsof -i tcp@%s:%d -t" % (SERVER_HOST, HTTPD_PORT)).split('\n')

  pids=[pid for pid in pids if pid]

  killPids(pids)

  if pids:
    time.sleep(2)
    print "Port should be free now."
  else:
    print "Noone is using the port."
  print "Check if port",HTTPD_PORT,"is really available."
  s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    try:
      s.setsockopt ( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind(('',HTTPD_PORT))
      s.listen(5)
      print "Port is available!"
    except socket.error:
      user=pwd.getpwuid(os.getuid())[0]    # cannot use os.getlogin() here
      print "Problem claiming port! Killing all python processes of user %s!" % user
      pids=commands.getoutput("pgrep -u %s python" % user).split('\n')
      pids=[pid for pid in pids if pid]
      killPids(pids)
      print "Port should now be available."
  finally:
    s.close()


def main(args):
  if len(args)>1:
    if args[1]=='check':
      checkServer()
    elif args[1] =='stop':
      force=False
      print "stopping server..." 
      try:
        daemon.startstop(stdout=SERVER_LOG,pidfile=SERVER_PID,action='stop')
      except daemon.DaemonizeError,x:
        print "POSSIBLE ERROR:",x
        force=True
      checkServer(force=force,restart=False)
      print "\nServer is not running anymore."
    elif args[1] =='force':
      print "INFO:forcing the start of another server<<"
      checkServer(force=True)
    else:
      print "Usage: %s [check|stop|force]" % args[0]
      print "(check will restart the server if it's down)"
  else:
    checkServer()


if __name__=="__main__":
  main(sys.argv)

