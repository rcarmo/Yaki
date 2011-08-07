#############################################################################
#
#	$Id: webform.py,v 1.11 2008/10/12 15:42:16 irmen Exp $
#	Form-related stuff (form parameters processing, file uploads)
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################


import os
import urllib
import copy
import cgi

#
#   Exception that can be raised if something went wrong.
#
class FormFileUploadError(Exception):
    pass


#
#   FormUploadedFile: all data you need to know about an uploaded file
#
class FormUploadedFile(object):
    def __init__(self, name, cgiFieldStorage):
        self.name=name
        self.file=cgiFieldStorage.file
        self.filename=os.path.basename(cgiFieldStorage.filename)
        self.disposition=cgiFieldStorage.disposition
        self.dispositionOptions=cgiFieldStorage.disposition_options
        self.mimeType=cgiFieldStorage.type
        self.typeOptions=cgiFieldStorage.type_options
    def __repr__(self):
        return str(self)
    def __str__(self):
        return "<uploaded file '"+self.filename+"' in field '"+self.name+"' at "+hex(id(self))+">"

#
#   The Request's FORM object (with the form parameters)
#   It's a dictionary parameter-->value
#   where value can be singular or a list of values.
#   Uploaded file attachments are treated differently!
#   (that will be FormUploadedFile instances).
#
class Form(dict):
    def __init__(self, cgiFieldStorage, encoding=None):
        for param in cgiFieldStorage.keys():
            value=cgiFieldStorage[param]
            # Find out what type of entry it is.
            # Also, if an (input-)encoding is given, decode the parameters into unicode.
            if type(value) is list:
                if encoding:
                    self[param.decode(encoding)]=[ mf.value.decode(encoding) for mf in value]
                else:
                    self[param]=[ mf.value for mf in value]
            elif value.file and value.filename:
                self[param]=FormUploadedFile(param,value)
            else:
                if encoding:
                    uparam = param.decode(encoding)
                    uvalue=value.value.decode(encoding)
                    self[uparam]=uvalue
                else:
                    self[param]=value.value

    def parseQueryArgs(self, queryargs):
        # this is used to parse any GET-style query args when the method was POST.
        # this is needed because of a problem in older versions of the cgi module.
        # (fixed in Python 2.6)
        extraParams={}
        for key,value in cgi.parse_qsl(queryargs):
            extraParams.setdefault(key,[]).append(value)
        for key in extraParams:
            if key in self:
                if not type(self[key]) is list:
                    self[key] = [self[key]]
                self[key].extend(extraParams[key])
            else:
                self[key]=extraParams[key]

    def simplifyValues(self):
        # every value that is a list with one element,
        # will be replaced by only that element.
        removelist=[]
        for (name, value) in self.iteritems():
            if type(value) is list:
                if len(value)==1:
                    self[name]=value[0]
                elif len(value)==0:
                    removelist+=name
        for name in removelist:
            del self[name]

    def urlencode(self):
        return urllib.urlencode(self)

    def copy(self):
        return copy.copy(self)    # make a copy of self, not only of the dict

