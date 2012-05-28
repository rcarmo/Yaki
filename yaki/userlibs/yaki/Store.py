#!/usr/bin/env python
# encoding: utf-8
"""
Store.py

Content store encapsulation (currently one folder per page with an index document)

Created by Rui Carmo on 2006-11-12.
Published under the MIT license.
"""

import logging
log=logging.getLogger("Snakelets.logger")

import os, stat, glob, codecs
import rfc822 # for basic parsing
import fs # filesystem abstractions
from fs.multifs import MultiFS
from fs.osfs import OSFS
from fs.zipfs import ZipFS
from yaki.Page import Page
from yaki.Utils import *

BASE_TYPES={
  "txt": "text/plain",
  "html": "text/html",
  "htm": "text/html",
  "md": "text/x-markdown",
  "mkd": "text/x-markdown",
  "markdown": "text/x-markdown",
  "textile": "text/x-textile"
}
BASE_FILENAMES=["index.%s" % x for x in BASE_TYPES.keys()]
BASE_PAGE = """From: %(author)s
Date: %(date)s
Content-Type: %(markup)s
Content-Encoding: utf-8
Title: %(title)s
Keywords: %(keywords)s
Categories: %(categories)s
Tags: %(tags)s
%(_headers)s

%(content)s
"""

def _fs_mtime(info):
     """
     Try multiple FS time representations until we get the closest thing to an mtime
     """
     for i,f in [('st_mtime',lambda x: x), ('modified_time',lambda x: time.mktime(x.timetuple())), ('created_time',lambda x: time.mktime(x.timetuple()))]:
          if i in info:
              return f(info[i])
     raise KeyError('Modification time not available')

class Store:
    """
    Wiki Store - abstracts actual storage and versioning
    """
    def __init__(self, path="space", ignore=['CVS', '.hg', '.svn', '.git', '.AppleDouble']):
        """
        Constructor
        """
        self.fs = MultiFS()
        # Mount the path we're given as a writable fs
        self.fs.addfs('root',OSFS(path,thread_synchronize=True),True)
        self.pages={}
        self.aliases={}
        self.dates={}
        self.ignore = ignore
    
    def getPath(self,pagename):
        """
        Append the store path to the pagename
        """
        # TODO: this will break with pyfilesystem - leaving it in temporarily to raise the proper exception
        return os.path.join(self.path, pagename)
    
    def date(self, pagename):
        """
        Retrieve a page's stored date (or fall back to mtime)
        """
        if pagename in self.dates.keys():
            return self.dates[pagename]
        else:
            return self.mtime(pagename)
  
    def mtime(self, pagename):
        """
        Retrieve modification time for the current revision of a given page by checking the folder modification time.
        Assumes underlying OS/FS knows how to properly update mtime on a folder.
        """
        if self.fs.exists(pagename):
            return _fs_mtime(self.fs.getinfo(pagename))
        return None
    
    def getAttachments(self, pagename, pattern = '*'):
        # TODO: check if os.path.basename might be required 
        attachments = filter(lambda x: not self.fs.isdir(x), self.fs.ilistdir(pagename, pattern))
        return attachments
          
    def isAttachment(self, pagename, attachment):
        """
        Checks if a given filename is actually attached to a page
        """
        attachment = os.path.join(targetpath,attachment)
        try:
            if self.fs.exists(attachment) and not self.fs.isdir(attachment):
              return True
        except:
            log.error("Bad attachment %s in %s" % (attachment, pagename))
        return False
  
    def getAttachmentFilename(self, pagename, attachment):
        """
        Returns the filename for an attachment
        """
        targetfile = os.path.join(targetpath,attachment)
        return targetfile
    
    def getRevision(self, pagename, revision = None):
        """
        Retrieve the specified revision from the store.
        
        At this point we ignore the revision argument
        (versioning will be added at a later date, if ever)
        """
        mtime = self.mtime(pagename)
        if mtime != None:
            for base in BASE_FILENAMES:
                targetfile = os.path.join(pagename,base)
                if self.fs.exists(targetfile):
                    mtime = self.mtime(targetfile)
                    break
            try:
                buffer = codecs.EncodedFile(self.fs.open(targetfile,'rb'),'utf-8').read()
                p = Page(buffer,BASE_TYPES[base.split('.',1)[1]])
    
                # If the page has no title header, use the path name
                if 'title' not in p.headers.keys():
                    p.headers['title'] = pagename
                p.headers['name'] = pagename
                
                # Now try to supply a sensible set of dates
                try:
                    # try parsing the date header
                    p.headers['date'] = parseDate(p.headers['date'])
                except:
                    # if there's no date header, use the file's modification time
                    # (if only to avoid throwing an exception again)
                    p.headers['date'] = mtime
                    pass
                # Never rely on the file modification time for last-modified
                # (otherwise SVN, Unison, etc play havoc with modification dates)
                try:
                    p.headers['last-modified'] = parseDate(p.headers['last-modified'])
                except:
                    p.headers['last-modified'] = p.headers['date']
                    pass
                self.dates[pagename] = p.headers['date']
                return p
            except IOError:
                raise IOError, "Couldn't find page %s." % (pagename)
        else:
            raise IOError, "Couldn't find page %s." % (pagename)
        return None
    
    def allPages(self):
        """
        Enumerate all pages and their last modification time
        """
        for path in self.fs.walkdirs('/'):
            pieces = path.split('/')
            # filter out paths containing SCM stuff
            if True in map(lambda x: x in pieces, self.ignore):
                continue
            for filename, info in self.fs.ilistdirinfo(path):
                for base in BASE_FILENAMES:
                    if os.path.basename(filename).lower() == base:
                        # cunningly reassemble the tailless list as the page path
                        self.pages[path[1:]] = _fs_mtime(info)
        
        for name in self.pages.keys():
            base = name.lower()
            if base in self.aliases.keys():
                if len(self.aliases[base]) > len(name):
                    self.aliases[base] = name
            else:
                self.aliases[base] = name        
            for replacement in ALIASING_CHARS:
                alias = name.lower().replace(' ',replacement)
                self.aliases[alias] = name
        return self.pages
    
    def updatePage(self, pagename, fields, base = "index.txt"):
        """
        Updates a given page, inserting a neutral text file by default
        """
        # TODO: this will need further revision (do we want a writable store?)
        targetpath = self.getPath(pagename)
        if(not self.fs.exists(targetpath)):
            self.fs.makedir(targetpath, True)
        filename = os.path.join(targetpath,base) 
        try:
            self.fs.open(filename, "wb").write((BASE_PAGE % fields).encode('utf-8'))
        except IOError:
            return None
        return True
    
    def addAttachment(self, pagename, filename, newbasename = None):
        # TODO: this will need further revision (do we want a writable store?)
        targetpath = self.getPath(pagename)
        if(not self.fs.exists(targetpath)):
            self.fs.makedir(targetpath, True)
        if newbasename:
            self.fs.copy(filename,os.path.join(targetpath,newbasename))
        else:
            self.fs.copy(filename,os.path.join(targetpath,os.path.basename(filename)))
  
#=================================

if __name__=="__main__":
  print "Initializing test store."
  s = Store('../../../pages/main')
  print s.allPages()
  print "Getting test page."
  r = s.getRevision('meta/Sandbox')
  if None != r:
    print r.raw
  else:
    print "Empty page."
