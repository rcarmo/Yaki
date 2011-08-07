#############################################################################
#
#	$Id: compiler.py,v 1.80 2008/10/12 15:42:16 irmen Exp $
#	Ypage compiler
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

#
#   This compiler translates Ypage files to Python source code.
#   It does NOT byte-compile the generated Python code, so in a way the
#   name 'compiler' is misleading.
#   The parser is used to parse the Ypage into an AST, and then a recursive
#   tree walking code generator walks the AST to generate Python source
#   code for the page.
#   The AST can be optimized a bit before translation (coalescing text nodes,
#   removing whitespace nodes etc).
#   Also some sanity checks are performed on the AST when the page is compiled,
#   so that the resulting source code will be a valid Ypage class.
#
#   The generated source is returned as a unicode string.
#   It still has to be compiled to byte code and then executed.
#   (the compiler doesn't do this by itself because it doesn't know or
#   care about the way the application wants to user or even store the
#   actual compiled code).
#

import parser
from tokenizer import TokenizerError
import sys, string, re, os, urllib



class CompilerError(Exception):
    def __str__(self):
        if len(self.args)>1:
            return str(self.args)
        else:
            return unicode(self.args[0]).encode("unicode-escape")

class PageCompiler:
    def __init__(self):
        pass

    def compilePage(self, filename, docrootPath, defaultOutputEncoding=None, defaultPageTemplate=None):
        self.declarations={}
        self.imports=[]
        self.gobbleWS=True
        self.outputEncoding_fromChild=False
        self.contentType=None
        self.contentDisposition=None
        self.allowCaching=None
        self.indentChars='\t' # we use tabs for indentation
        self.session=None
        self.authorized=None # authorized roles
        self.authmethod=None # authentication method
        self.authmethodargs=None # args for the auth method
        self.errorpage=None # custom error page
        self.pagemethod="create"  # name used for the page creation method
        self.baseclasses=[]
        self.methods=[]
        self.pageTemplate=defaultPageTemplate
        self.pageTemplateArgs={}
        self.docrootPath=docrootPath
        self.inputEncoding, self.outputEncoding=parser.determineInputOutputEncodings(filename)
        if not self.outputEncoding:
            self.outputEncoding=defaultOutputEncoding
        self.tpl_outputEncoding=self.tpl_contentType=None
        try:
            try:
                # 1. open the page source file
                pageSourceStream=None
                if self.inputEncoding:
                    import codecs
                    pageSourceStream=codecs.open(filename,mode="rb",encoding=self.inputEncoding)
                else:
                    # use regular file because input encoding is default (not specified).
                    pageSourceStream=file(filename,"r")
                # 2. parse the page source
                parse=parser.Parser(pageSourceStream, filename, self.inputEncoding)
                syntaxtree=parse.parse()
                self.outputEncoding_fromChild=parse.outputEncoding_fromChild
            finally:
                # 3. close the page source file
                if pageSourceStream:
                    pageSourceStream.close()        # otherwise .y file remains opened until GC'd.
                del pageSourceStream

            # 4. generate python code
            (result,indent) = self.generateCode(syntaxtree,0)
            return result  # return the Unicode string

        except (TokenizerError, parser.ParserError), px:
            sys.exc_clear()
            raise CompilerError(px)

    def _addTextBlock(self, astlist, child):
        if len(astlist)>0 and isinstance(astlist[-1], parser.TextBlock):
            astlist[-1].text+=child.text
        else:
            astlist.append(child)

    def optimize(self, ast):
        self.hasText=False  # we have not outputted any text yet
        return self._optimize(ast)

    def _optimize(self,ast):
        # this optimizes the raw syntax tree into something more compact
        optimized=[]
        prev=None
        for child in ast:
            if isinstance(child, parser.Script):
                scriptchildren=self._optimize(child)
                if scriptchildren or not child.isStartOfBlock():
                    optimized.append(parser.Script(child.text, scriptchildren))
                else:
                    raise CompilerError("script block contents is empty (after optimalization): "+child.text[:20]+"...")
            elif isinstance(child, parser.Comment):
                optimized.append(child)
            elif isinstance(child, parser.Expression):
                # url() and asset() calls are assumed to return string
                child.assumeString = re.match(r"\s*url\(.+\)\s*$", child.text) or re.match(r"\s*asset\(.+\)\s*$", child.text)
                optimized.append(child)
            elif isinstance(child, parser.Whitespace):
                if not self.gobbleWS:
                    self._addTextBlock(optimized, child)
            elif isinstance(child, parser.TextBlock):
                if self.gobbleWS and not isinstance(prev, parser.Expression):
                    newTxt=child.text.strip()
                    if newTxt:
                        if self.hasText:   # only add a space when NOT first text element
                            if child.text[0] in string.whitespace:
                                newTxt=' '+newTxt   # add a single space instead
                        if child.text[-1] in string.whitespace:
                            newTxt+=' '    # add a single space instead
                        self._addTextBlock(optimized, parser.TextBlock(newTxt))
                        self.hasText=True # we have outputted some text now
                else:
                    self._addTextBlock(optimized, child)
            else:
                optimized.append(child)
            prev=child
        ast[:]=optimized
        return ast

    def readTemplateDecls(self, tplpath):
        pageSourceStream=file(tplpath,"r")
        parse=parser.Parser(pageSourceStream, tplpath, None)
        return parse.parseDeclarationsOnly()

    def processDeclarations(self, syntaxtree):
        gatheredWhitespace=""
        while syntaxtree and ( isinstance(syntaxtree[0],  parser.Declaration) or isinstance(syntaxtree[0], parser.Whitespace) ):
            c=syntaxtree.pop(0) # get next AST node
            if isinstance(c, parser.Whitespace):
                gatheredWhitespace += c.text
                continue

            c.name=c.name.lower()

            if c.name=='import':
                if c.value.split()[0] in ("import", "from"):
                    self.imports.append(c.value)
                else:
                    raise CompilerError("invalid import statement: '"+c.value+"'")
            elif c.name=='gobblews':
                if c.value.lower() in ('yes','no'):
                    self.gobbleWS = c.value.lower()=='yes'
                else:
                    raise CompilerError("gobblews must be yes or no")
            elif c.name=='allowcaching':
                if c.value.lower() in ('yes','no'):
                    self.allowCaching = c.value.lower()=='yes'
                else:
                    raise CompilerError("allowcaching must be yes or no")
            elif c.name=='session':
                value=c.value.lower()
                if value in ('yes', 'no', 'user', 'valid', 'dontcreate'):
                    self.session = value
                    # NOTICE: a non-user session will let Snakelets ignore any signin page.
                else:
                    raise CompilerError("session must be yes, no, valid, dontcreate or user")
            elif c.name=='outputencoding':
                if parser.stringInQuotes(c.value):
                    c.value=c.value[1:-1]
                if self.outputEncoding!=c.value:
                    if self.outputEncoding_fromChild:   # parsed document's encoding was changed by an included child document
                        self.outputEncoding=c.value
                    else:
                        raise RuntimeError("output encoding was parsed wrongly")
            elif c.name=='inputencoding':
                if parser.stringInQuotes(c.value):
                    c.value=c.value[1:-1]
                if self.inputEncoding!=c.value:
                    raise RuntimeError("input encoding was parsed wrongly")
            elif c.name=='contenttype':
                if parser.stringInQuotes(c.value):
                    c.value=c.value[1:-1]
                self.contentType=c.value
            elif c.name=='disposition':
                self.contentDisposition=c.value
            elif c.name=='indent':
                v=c.value.lower()
                if v=='8spaces':
                    self.indentChars=' '*8
                if v=='4spaces':
                    self.indentChars=' '*4
                elif v=='tab':
                    self.indentChars='\t'
                else:
                    raise CompilerError("indent type must be tab or 4spaces or 8spaces")
            elif c.name=='errorpage':
                if parser.stringInQuotes(c.value):
                    c.value=c.value[1:-1]
                self.errorpage=c.value
            elif c.name=='pagemethod':
                self.pagemethod=c.value.strip()
            elif c.name=='inherit':
                self.baseclasses=[clz.strip() for clz in c.value.split(',')]
            elif c.name=='pagetemplate':
                if parser.stringInQuotes(c.value):
                    c.value=c.value[1:-1]
                page=c.value.strip()
                if page.lower()=='none':
                    page=None
                self.pageTemplate=page
                if self.pageTemplate and self.pageTemplate.lower() != 'none':
                    tplpath = os.path.join( self.docrootPath, urllib.url2pathname(self.pageTemplate) )
                    try:
                        decls=self.readTemplateDecls(tplpath)
                    except EnvironmentError,x:
                        raise CompilerError("cannot load page template file '%s': %s" % (self.pageTemplate,x))
                    else:
                        for d in decls:
                            d.name=d.name.lower()
                            if parser.stringInQuotes(d.value):
                                d.value=d.value[1:-1]
                            if d.name=="contenttype":
                                self.tpl_contentType=d.value
                            elif d.name=="outputencoding":
                                self.tpl_outputEncoding=d.value
            elif c.name=='pagetemplatearg':
                if parser.stringInQuotes(c.value):
                    c.value=c.value[1:-1]
                (name,value)=c.value.split('=',1)
                self.pageTemplateArgs[name]=value
            elif c.name=='authorized':
                self.authorized=set(c.value.split(','))
                if self.session and self.session!='user':
                    raise CompilerError("authorized declaration requires sessiontype 'user'")
                self.session="user"     # implied by the authorized roles.
            elif c.name=='authmethod':
                if ';' in c.value:
                    self.authmethod, self.authmethodargs = c.value.split(';',1)
                else:
                    self.authmethod=c.value
            elif c.name=='method':
                self.methods.append(c.value)
            else:
                raise CompilerError("unknown declaration: %s=%s" % (c.name, c.value))

        self.session=self.session or "yes" # default = yes, use session

        # NOTE: never return whitespace between declarations...
        #if self.gobbleWS:
        #   return ""
        #return gatheredWhitespace
        return ""

    
    # The actual code generation.
    # Returns unicode string that is the code generated from c,
    # where parameter c is a node in the AST tree.
    # (this is a recursive call).
    def generateCode(self,c,blockindent):
        (code, indent)=self._generateCode(c,blockindent)
        code.insert(0, u"# code generated by Snakelets Ypage compiler")
        code.insert(1, u"# -*- coding: UTF-8 -*-")
        code = '\n'.join(code)+'\n'
        return (code.encode("UTF-8"), indent)
    def _generateCode(self,c,blockindent):
        indent=self.indentChars*blockindent
        code=[]  # returns list-of-lines-of-code

        if isinstance(c, parser.Document):
            gatheredWhitespace = self.processDeclarations(c)
            if gatheredWhitespace and not self.gobbleWS:
                c.insert(0,parser.Whitespace(gatheredWhitespace))
            # optimize the raw syntax tree to something more compact
            c=self.optimize(c)
            code.append("from snakeserver.YpageEngine import Ypage")
            # page imports
            for imp in self.imports:
                code.append(imp)
            code.append("sourcelines="+str(c.endlocation[0]))   # for stats
            if self.baseclasses:
                code.append("import types")
                code.append("for clazz in ['"+ "','".join(self.baseclasses) +"']:")
                code.append(self.indentChars+"short=clazz.split('.')[-1]")
                code.append(self.indentChars+"package=clazz[:-len(short)-1]")
                code.append(self.indentChars+"if not vars().has_key(short):")
                code.append(self.indentChars*2+"if package: exec('from %s import %s' % (package,short))")
                code.append(self.indentChars*2+"else: exec('from %s import %s ' % (short,short))")
                code.append(self.indentChars+"if not type(vars()[short]) in (types.ClassType, types.TypeType): raise TypeError('invalid page inheritance: '+short+' is not a class')")
                code.append("")
                code.append("class Page(Ypage,"+','.join([clazz.split('.')[-1] for clazz in self.baseclasses])+"):")
            else:
                code.append("class Page(Ypage):")

            # add snakelet control methods
            if self.session=='no': session='SESSION_NOT_NEEDED'
            elif self.session=='yes': session='SESSION_WANTED'
            elif self.session=='valid': session='SESSION_REQUIRED'
            elif self.session=='dontcreate': session='SESSION_DONTCREATE'
            elif self.session=='user': session='SESSION_LOGIN_REQUIRED'
            else:
                raise CompilerError('invalid session selector: '+self.session)
            code.append(self.indentChars+"def requiresSession(self): return self."+session)

            if self.authorized:
                code.append(self.indentChars+("def getAuthorizedRoles(self): return set(%r)" % (tuple(self.authorized), ) ) )
            if self.authmethod:
                code.append(self.indentChars+("def getAuthMethod(self): return (%r,%r)" % (self.authmethod, self.authmethodargs)) )
            self.outputEncoding=self.outputEncoding or self.tpl_outputEncoding
            if self.outputEncoding:
                code.append(self.indentChars+("def getPageEncoding(self): return %r" % self.outputEncoding) )
            self.contentType=self.contentType or self.tpl_contentType
            if self.contentType or self.contentDisposition:
                code.append(self.indentChars+("def getPageContentTypeAndDisposition(self): return %r,%r" % (self.contentType, self.contentDisposition)) )
            if self.allowCaching:
                code.append(self.indentChars+("def allowCaching(self): return %r" % self.allowCaching) )
            code.append(self.indentChars+"_ypage_template=%r" % self.pageTemplate or None)
            if not self.pageTemplateArgs:
                self.pageTemplateArgs=None
            code.append(self.indentChars+"_ypage_templateargs=%r" % self.pageTemplateArgs)

            # add page methods
            for meth in self.methods:
                meth=meth.strip().split('\n')
                code.append(self.indentChars+"def "+meth[0])
                for l in meth[1:]:
                    l=l.rstrip()
                    if l and l[0] not in (' ', '\t'):
                        raise CompilerError("indentation error in custom page method '%s'" % meth[0])
                    code.append(self.indentChars*2+l[1:])

            # generate page method
            code.append(self.indentChars+"def "+self.pagemethod+"(self,out,_request,_response,templatedPage=None):")
            code.append(self.indentChars*2+"url=_request.webapp.mkUrl")
            code.append(self.indentChars*2+"asset=_request.webapp.mkAssetUrl")
            code.append(self.indentChars*2+"_w=out.write")
            if self.errorpage:
                code.append(self.indentChars*2+"self.setErrorPage('"+self.errorpage+"')")

            for child in c:
                (subcode, indent) = self._generateCode(child, blockindent+2)
                code.extend(subcode)
                if indent>0:
                    indent-=3   # de-indent 1, plus the additinal 2 indents added above
                blockindent=indent
        elif isinstance(c,  parser.Declaration):
            if c.name=='import':
                if c.value.split()[0] in ("import", "from"):
                    self.imports.append(c.value)
                else:
                    raise CompilerError("invalid import statement: '"+c.value+"'")
            self.declarations[c.name]=c.value
        elif isinstance(c,parser.Comment):
            code.append(indent+'# '+c.text)
        elif isinstance(c,parser.URLCall):
            prefix=''
            if type(c.url)==unicode:
                prefix='u'
            # do not use _w, because include writes to stream by itself.
            code.append(indent+('self.include(%s"%s", _request, _response)' % (prefix, c.url) ) )
        elif isinstance(c,parser.URLForward):
            prefix=''
            if type(c.url)==unicode:
                prefix='u'
            code.append(indent+('self.Yredirect(%s"%s")' % (prefix,c.url) ) )
        elif isinstance(c,parser.HTTPRedirect):
            prefix=''
            if type(c.url)==unicode:
                prefix='u'
            code.append(indent+('self.Yhttpredirect(%s"%s")' % (prefix,c.url) ) )
        elif isinstance(c,parser.TextBlock):
            text=repr(c.text) # escape the special characters such as ", ', \n
            if not isinstance(c,parser.Whitespace) or not self.gobbleWS:
                code.append(indent+'_w('+text+')')
        elif isinstance(c, parser.Expression):
            if c.assumeString:
                # the optimizer signals that no string conversion is needed
                code.append(indent + "_w("+c.text+")")
            else:
                if self.outputEncoding:
                    code.append(indent + "_w(unicode("+c.text+"))")
                else:
                    code.append(indent + "_w(str("+c.text+"))")
        elif isinstance(c, parser.Script):
            lines=[indent+line for line in c.text.split('\n')]
            code.extend(lines)
            newblockindent=blockindent+1
            if lines:
                # determine the 'real' indentation that we have at this point,
                # but only if the previous
                lastline=lines[-1]
                if lastline.endswith(':'):
                    newblockindent = self.determineIndent(lastline,blockindent)+1
            for child in c:
                (subcode,indent) = self._generateCode(child, newblockindent)
                code.extend(subcode)
            return code,newblockindent
        elif isinstance(c, parser.InsertPageBody):
            code.append(indent+"if templatedPage:")
            if self.errorpage:
                # also use a defined errorpage for the actual page (it can set another one itself)
                code.append(indent*2+"templatedPage.setErrorPage('"+self.errorpage+"')")
            code.append(indent*2+"templatedPage.create(out, _request, _response)")
            code.append(indent+"else: _w('{no templated page available}')")
        else:
            raise CompilerError("invalid syntax element "+repr(c))

        return code,0


    def determineIndent(self, lastline, blockindent):
            indentchars=len(self.indentChars)*blockindent
            lastline=lastline[indentchars:]
            extraindent=0
            while lastline.startswith(self.indentChars):
                lastline=lastline[len(self.indentChars):]
                extraindent+=1
            return blockindent+extraindent


def main(args):
    compiler=PageCompiler()
    if len(args)!=3:
        print "usage: python "+args[0]+" page.y output"
        print "where output is a file or - for stdout"
        raise SystemExit

    if args[2]=='-':
        output=sys.stdout
    else:
        output=file(args[2],"wb")

    result = compiler.compilePage(args[1])

    output.write(result.encode('iso-8859-1','replace'))

if __name__=="__main__":
    main(sys.argv)

