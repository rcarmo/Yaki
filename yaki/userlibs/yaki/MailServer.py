#!/usr/bin/env python
# encoding: utf-8
"""
MailServer.py

Created by Rui Carmo on 2007-04-21.
Published under the MIT license.
"""
import sys, asyncore, asynchat, threading, socket
import smtpd, email, mimetypes
import base64, time, StringIO
#import Store

NEWLINE = '\n'
EMPTYSTRING = ''
COMMASPACE = ', '

__version__ = 'Yaki SMTP Mail Listener'

class SMTPAuthChannel(asynchat.async_chat):
  """
  Replace SMTPChannel completely for future expansion
  """
  COMMAND = 0
  DATA = 1

  def __init__(self, server, conn, addr, authdata):
    asynchat.async_chat.__init__(self, conn)
    defaults = {
      'authenticated': False,
      'authdata': authdata,
      'server': server,
      'conn': conn,
      'addr': addr,
      'line': [],
      'state': self.COMMAND,
      'greeting': 0,
      'mailfrom': None,
      'rcpttos': [],
      'data': '',
      'fqdn': socket.getfqdn(),
      'peer': conn.getpeername()
    }
    for k in defaults.keys():
      setattr(self,k,defaults[k])
    self.push('220 %s ESMTP' % (self.fqdn))
    self.set_terminator('\r\n')

  # Overrides base class for convenience
  def push(self, msg):
    asynchat.async_chat.push(self, msg + '\r\n')

  # Implementation of base class abstract method
  def collect_incoming_data(self, data):
    self.line.append(data)

  # Implementation of base class abstract method
  def found_terminator(self):
    line = EMPTYSTRING.join(self.line)
    self.line = []
    if self.state == self.COMMAND:
      if not line:
        self.push('500 Error: bad syntax')
        return
      method = None
      i = line.find(' ')
      if i < 0:
        command = line.upper()
        arg = None
      else:
        command = line[:i].upper()
        arg = line[i+1:].strip()
      method = getattr(self, 'smtp_' + command, None)
      if not method:
        self.push('502 Error: command "%s" not implemented' % command)
        return
      method(arg)
      return
    else:
      if self.state != self.DATA:
        self.push('451 Internal confusion')
        return
      # Remove extraneous carriage returns and de-transparency according
      # to RFC 821, Section 4.5.2.
      data = []
      for text in line.split('\r\n'):
        if text and text[0] == '.':
          data.append(text[1:])
        else:
          data.append(text)
      self.data = NEWLINE.join(data)
      status = self.server.process_message(self.peer,
                                           self.mailfrom,
                                           self.rcpttos,
                                           self.data)
      self.rcpttos = []
      self.mailfrom = None
      self.state = self.COMMAND
      self.set_terminator('\r\n')
      if not status:
          self.push('250 Ok')
      else:
          self.push(status)
  
  def smtp_AUTH(self, arg):
    try:
      (method,data) = arg.split(' ')
      if method.lower() == 'plain':
        (authorize,user,password) = base64.decodestring(data).split('\x00')
        if self.authdata[user] == password:
          self.authenticated = True
          self.push('235 Authentication successful.')
          return
        else:
          self.push('530 Access Denied')
          return
    except:
      self.push('535 Invalid Auth Data')
    
  def smtp_MAIL(self, arg):
    if not self.authenticated:
      self.push('530 Authentication Required')
      return
    address = self.getaddr('FROM:', arg)
    if not address:
      self.push('501 Syntax: MAIL FROM:<address>')
      return
    if self.mailfrom:
      self.push('503 Error: nested MAIL command')
      return
    self.mailfrom = address
    self.push('250 Ok')
  
  def smtp_EHLO(self, arg):
    """Patch initial greeting"""
    if not arg:
      self.push('501 Syntax: EHLO hostname')
      return
    if self.greeting:
      self.push('503 Duplicate HELO/EHLO')
    else:
      self.greeting = arg
      self.push('250-%s' % self.fqdn)
      self.push('250 AUTH PLAIN')

  def smtp_RCPT(self, arg):
    if not self.mailfrom:
      self.push('503 Error: need MAIL command')
      return
    address = self.getaddr('TO:', arg)
    if not address:
      self.push('501 Syntax: RCPT TO: <address>')
      return
    self.rcpttos.append(address)
    self.push('250 Ok')

  def smtp_RSET(self, arg):
    if arg:
      self.push('501 Syntax: RSET')
      return
    self.mailfrom = None
    self.rcpttos = []
    self.data = ''
    self.state = self.COMMAND
    self.push('250 Ok')

  def smtp_DATA(self, arg):
    if not self.rcpttos:
      self.push('503 Error: need RCPT command')
      return
    if arg:
      self.push('501 Syntax: DATA')
      return
    self.state = self.DATA
    self.set_terminator('\r\n.\r\n')
    self.push('354 End data with <CR><LF>.<CR><LF>')
    
  def smtp_NOOP(self, arg):
    if arg:
      self.push('501 Syntax: NOOP')
    else:
      self.push('250 Ok')

  def smtp_QUIT(self, arg):
    # args is ignored
    self.push('221 Bye')
    self.close_when_done()
        
  def getaddr(self, keyword, arg):
    address = None
    keylen = len(keyword)
    if arg[:keylen].upper() == keyword:
      address = arg[keylen:].strip()
      if not address:
        pass
      elif address[0] == '<' and address[-1] == '>' and address != '<>':
        # Addresses can be in the form <person@dom.com> but watch out
        # for null address, e.g. <>
        address = address[1:-1]
    return address


class SMTPListener(smtpd.SMTPServer):

  def __init__( self, *args, **kwargs):
    smtpd.SMTPServer.__init__( self, *args, **kwargs )

  def handle_accept(self):
    """Patch superclass"""
    conn, addr = self.accept()
    channel = SMTPAuthChannel(self, conn, addr, self.authdata)

  def process_message(self, peer, mailfrom, rcpttos, data):
    """
    http://docs.python.org/lib/module-email.message.html
    """
    msg = email.message_from_string(data)
    count = 1
    cids = {}
    for part in msg.walk():
      if part.get_content_maintype() == 'multipart':
        continue
      if part.get_content_type() == "text/html":
        soup = part.get_payload(decode = True)
        print soup
      print part
      filename = part.get_filename()
      if not filename:
        ext = mimetypes.guess_extension(part.get_content_type())
        print ext
        if ext in ['.jpg','.gif','.png']:
          filename = "Image%d%s" % (count, ext)
          count = count + 1
          cid = part['Content-ID']
          if cid[0] == '<':
            cid = cid[1:len(cid)-1]
          cids[cid] = filename
      print filename          
    print '------------ END MESSAGE ------------'
    print cids
      

class YakiSMTPServer(threading.Thread):
  _stop_poll_time = 1

  def __init__( self, authdata = None, host = '', port = 8025, mailboxFile = None, threadName = None ):
    self.authdata = authdata
    self.initThread( threadName )
    self.initSink(host, port)

  def initThread( self, threadName ):
    self._stopevent = threading.Event()
    self.threadName = threadName
    if self.threadName is None:
      self.threadName = YakiSMTPServer.__class__
    threading.Thread.__init__( self, name = self.threadName )
    
  def login(self, user, password):
    if self.authdata[user] == password:
      return true
    return false
      
  def initSink( self, host, port ):
    self.sink = SMTPListener( ( host, port ), None )
    # minor kludge to avoid messing with params
    self.sink.authdata = self.authdata
                    
  def run(self):
    while not self._stopevent.isSet():
      asyncore.loop(timeout = YakiSMTPServer._stop_poll_time)

  def stop( self, timeout=None ):
    self._stopevent.set()
    threading.Thread.join( self, timeout )
    self.sink.close()
        
if __name__ == "__main__":
    sink = YakiSMTPServer( {'test':'password'}, '' )
    sink.start()
    while True:
      time.sleep( 1 )

