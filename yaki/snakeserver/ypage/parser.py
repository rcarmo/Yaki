#############################################################################
#
#	$Id: parser.py,v 1.41 2006/05/18 10:56:41 irmen Exp $
#	Ypage parser
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

#
#   This parser takes tokens and converts them to an Abstract Syntax Tree
#   of the Ypage. It also checks the syntax of the document.
#   The parser is a hand crafted recursive-descent parser.
#

import types
import os
import codecs
import re
import tokenizer    # do not confuse this with tokenize from the std lib


class ParserError(Exception):
    def __init__(self, msg, linenum=None):
        if linenum:
            msg = msg+" @"+str(linenum)
        Exception.__init__(self, unicode(msg).encode("unicode-escape") )

    
def isWhitespace(text):
    return type(text) in types.StringTypes and (len(text)==0 or text.isspace())

def stringInQuotes(txt):
    if txt and len(txt)>=2:
        if txt[0] in ( '\'', '"') and txt[-1] in ( '\'', '"'):
            return True
        if txt[0] in ( '\'', '"') or txt[-1] in ( '\'', '"'):
            raise ParserError("invalidly quoted string: "+txt)
    return False

# the objects of the AST

class AbstractSyntaxElement:
    def __str__(self):
        return repr(self)
    def __repr__(self):
        return "<"+self.__class__.__name__+">"
        
class Declaration(AbstractSyntaxElement):
    def __init__(self, name, value):
        self.name=name.strip()
        self.value=value.strip()
        
class TextBlock(AbstractSyntaxElement):
    def __init__(self, text):
        self.text=text
    def mergeText(self,text):
        self.text+=text

class Whitespace(TextBlock):
    pass

class InsertPageBody(AbstractSyntaxElement):
    pass


class Comment(AbstractSyntaxElement):   # NO TextBlock!
    def __init__(self, text):
        self.text=text
    
class URLCall(AbstractSyntaxElement):   # NO TextBlock!
    def __init__(self, url):
        self.url=url

class URLForward(AbstractSyntaxElement):   # NO TextBlock!
    def __init__(self, url):
        self.url=url

class HTTPRedirect(AbstractSyntaxElement):   # NO TextBlock!
    def __init__(self, url):
        self.url=url

class Expression(AbstractSyntaxElement):
    def __init__(self, text):
        self.text=text.strip()

class Script(AbstractSyntaxElement, list):
    def __init__(self, text, lst=None, stripIndent=False):
        list.__init__(self,lst or [])
        self.text=text.rstrip()
        if stripIndent:
            self.text=self.stripIndent(self.text)
    def stripIndent(self, text):
        # strip starting indents
        lines=text.split('\n')
        if lines:
            if not lines[0]:
                del lines[0]
            if not lines:
                return ''   # no script content at all... whatever ;-)
            indent=len(lines[0])-len(lines[0].lstrip())
            if indent:
                lines2=[]
                # strip indent from all lines
                # if we strip something that is not whitespace, we have an error
                for line in lines:
                    lines2.append(line[indent:])
                    if line[:indent].strip():
                        raise ParserError("script block indentation error")
                lines=lines2
                # lines=[line[indent:] for line in lines]
        return '\n'.join(lines)
    def __repr__(self):
        s=["<Script @%d:" % id(self)]
        for c in self:
            s.append(",")
            s.append(repr(c))
        s.append('/Script>')
        return ''.join(s)
    def isStartOfBlock(self):
        # if it ends with a : or with a : followed by a comment, it's a block start
        return self.text.endswith(':') or re.match("[^:#]*:[ \t]*(#.*)?$", self.text) is not None
    def isEndScript(self):
        return self.text=="end"
    def isEndAndNewBlock(self):
        return re.match(r"^else:",self.text) or re.match(r"^elif\s.+:",self.text)
        
class ScriptEndBlock(AbstractSyntaxElement,list):
    def __init__(self, content=None):
        if content is not None:
            self.append(content)
        
class Document(AbstractSyntaxElement, list):
    def __repr__(self):
        s=["[DOCUMENT:"]
        for c in self:
            s.append(",")
            s.append(repr(c))
        s.append(']')
        return ''.join(s)
    

# Scans the file for input and output encoding declarations.
def determineInputOutputEncodings(filename):
    inputEnc=outputEnc=None
    for line in file(filename,"r").readlines(1000)[:10]: # first 10 lines
        m=re.match(r".*<%@\s*(.+)\s*=\s*(.+)\s*%>\s*$", line)
        if m:
            (name,value)=m.groups()
            name=name.lower()
            if name in ('inputencoding','outputencoding'):
                if stringInQuotes(value):
                    value=value[1:-1]
                if name=='inputencoding':
                    inputEnc=value
                elif name=='outputencoding':
                    outputEnc=value
    return (inputEnc, outputEnc)


# The parser.
# Parses a tokenized stream into a AST, with a few
# syntax checks along the way.

# <ypage> --> DeclarationBlock DocBody <None>
# DeclarationBlock --> (WS Declaration)*
# DocBody --> (Text | Comment | Expression ) *

class Parser(object):
    def __init__(self, stream, filename, inputEncoding):
        self.tokenizer=tokenizer.Tokenizer(stream,filename)
        self.fileLocation = os.path.dirname(filename)
        self.inputEncoding=inputEncoding
        self.outputEncoding_fromChild = False
        self.tokens=self.tokenizer.getTokens()
        self.currentToken=None
        self.previousToken=None
        self.scriptNesting=0
        self.nextToken()
        self.declarations=[]
        self.includedDeclarations=[]
        
    def nextToken(self):
        try:
            self.previousToken=self.currentToken
            self.currentToken=self.tokens.next()
            return self.currentToken
        except StopIteration:
            # end of input
            self.currentToken=None
            return None
    def undoToken(self):
        self.currentToken, self.previousToken = self.previousToken, None
        
    def parseDeclarationsOnly(self):
        # only read and parse the declarations at the top of the file, return list of decls
        ast=Document()
        if self.currentToken==tokenizer.TOK_COMMENTOPEN:   # if ypage starts with a comment, skip it.
            self.skipComment() 
        return [d for d in self.parseDeclarationBlock() if isinstance(d, Declaration)]
        
    def parse(self):
        # fully parse the ypage source file.
        ast=Document()
        if self.currentToken==tokenizer.TOK_COMMENTOPEN:   # if ypage starts with a comment, skip it.
            self.skipComment() 
        self.declarations = self.parseDeclarationBlock()
        body = self.parseDocBody()
        ast.extend(body)
        if self.currentToken is None:
            self.declarations.extend(self.includedDeclarations)
            self.declarations.reverse()
            for d in self.declarations:
                ast.insert(0,d)   # place declarations at the front.
            ast.endlocation=self.tokenizer.getLocation()
            return ast
        else:
            raise ParserError("trailing garbage or wrong script tag", self.tokenizer.getLocationStr())

    def processWhitespaceAndComments(self):
        ast=[]
        while isWhitespace(self.currentToken) or self.currentToken==tokenizer.TOK_COMMENTOPEN:
            self.skipComment()
            if isWhitespace(self.currentToken):
                ast.append(Whitespace(self.currentToken))
                self.nextToken()
            else:
                break
        return ast
    
    def skipComment(self):
        if self.currentToken==tokenizer.TOK_COMMENTOPEN:
            while self.currentToken!=tokenizer.TOK_COMMENTCLOSE:
                self.nextToken()
                if not self.currentToken:
                    raise ParserError("missing comment closing tag", self.tokenizer.getLocationStr())
            self.nextToken() # skip the comment closing tag
                
                
    # Returns the parsed declarations in the DeclarationBlock at the
    # beginning of the document. On exit, the curToken is the first
    # non-whitespace token (or None at EOF).
    # (the parsed decaration AST also contains embedded whitespace!)
    def parseDeclarationBlock(self):
        ast=[]
        while self.currentToken==tokenizer.TOK_DECLARATIONOPEN or type(self.currentToken) in types.StringTypes:
            ast.extend(self.processWhitespaceAndComments())
            if self.currentToken==tokenizer.TOK_DECLARATIONOPEN:
                self.nextToken()
                if type(self.currentToken) in types.StringTypes:
                    decl=self.currentToken.split('=',1)
                    if len(decl)!=2:
                        raise ParserError("invalid declaration, must be decl=value", self.tokenizer.getLocationStr())
                    decl = Declaration(decl[0].strip(), decl[1].strip())
                    if not decl.name or not decl.value:
                        raise ParserError("invalid declaration, must be decl=value", self.tokenizer.getLocationStr())
                    ast.append(decl)
                    if self.nextToken()==tokenizer.TOK_SCRIPTCLOSE:
                        self.nextToken()
                    else:
                        raise ParserError("close token expected", self.tokenizer.getLocationStr())
                else:
                    raise ParserError("text expected", self.tokenizer.getLocationStr())
            else:
                # it is not a decl, we must be finished
                break
        return ast


    
    # DocBody        --> (Text | Comment | Expression | Script | Instruction ) *
    # DocBodyInBlock --> (Text | Comment | Expression | No_EndBlock_Script ) *
    def parseDocBody(self, inBlock=False):
        ast=[]
        while True:
            if type(self.currentToken) in types.StringTypes:        # Text
                ast.append(TextBlock(self.currentToken))
                self.nextToken()
            elif self.currentToken==tokenizer.TOK_COMMENTOPEN:
                self.skipComment()
            elif self.currentToken==tokenizer.TOK_EXPRESSIONOPEN:
                ast.append(self.parseExpression())
            elif self.currentToken==tokenizer.TOK_SCRIPTOPEN:
                if inBlock:
                    script=self.parseScript()
                    if script[0].isEndScript(): 
                        return ast,None
                    elif script[0].isEndAndNewBlock():
                        return ast,script
                    ast.extend(script)
                else:
                    script=self.parseScript()
                    if len(script)==1:
                        scripttxt=script[0].text.lower()
                        if scripttxt=="end":
                            raise ParserError("block ended while not in block", self.tokenizer.getLocationStr())
                        if scripttxt.startswith("else:") or scripttxt.startswith("elif:"):  # XXX hack-ish
                            raise ParserError("else or elif outside if", self.tokenizer.getLocationStr())
                    ast.extend(script)
            elif self.currentToken==tokenizer.TOK_INSTRUCTIONOPEN:
                # processing instruction
                self.nextToken()
                if type(self.currentToken) in types.StringTypes:
                    if '=' in self.currentToken:
                        instruction, value = self.currentToken.split('=',1)
                    else:
                        instruction, value = self.currentToken,''
                    self.processInstruction(instruction.lower(), value, ast)
                    if self.nextToken()==tokenizer.TOK_SCRIPTCLOSE:
                        self.nextToken()
                    else:
                        raise ParserError("close token expected", self.tokenizer.getLocationStr())
                else:
                    raise ParserError("text expected", self.tokenizer.getLocationStr())
            elif self.currentToken and type(self.currentToken) not in types.StringTypes:
                raise ParserError("normal text expected instead of tag", self.tokenizer.getLocationStr())
            else:
                # end of docbody
                break
        return ast     # yes, this is correct (pychecker)
    
    # Expression -> ExpressionOpen TextBlock ExpressionClose
    def parseExpression(self):
        if self.currentToken==tokenizer.TOK_EXPRESSIONOPEN:
            self.nextToken()
            if type(self.currentToken) in types.StringTypes:
                expr=Expression(self.currentToken)
                self.nextToken()
                if self.currentToken==tokenizer.TOK_SCRIPTCLOSE:
                    self.nextToken()
                    return expr
                else:
                    raise ParserError("expression close expected", self.tokenizer.getLocationStr())
            else:
                raise ParserError("text expected", self.tokenizer.getLocationStr())
        else:
            raise ParserError("expression expected", self.tokenizer.getLocationStr())

    
    # Script --> ScriptFragment | ScriptBlock
    # ScriptFragment --> ScriptOpen text-without-: ScriptClose
    def parseScript(self):
        if self.currentToken==tokenizer.TOK_SCRIPTOPEN:
            self.nextToken()
            if type(self.currentToken) in types.StringTypes:
                try:
                    scriptNode=Script(self.currentToken, stripIndent=True)
                except ParserError,px:
                    raise ParserError(str(px), self.tokenizer.getLocationStr())
                closeTok = self.nextToken()
                if closeTok in (tokenizer.TOK_SCRIPTCLOSE, tokenizer.TOK_SCRIPTCLOSEKEEPB):
                    self.nextToken()
                    if closeTok==tokenizer.TOK_SCRIPTCLOSEKEEPB or scriptNode.isStartOfBlock():
                        newscript=self.parseScriptBlock(scriptNode)
                        if newscript is not None:
                            ast=[scriptNode]
                            ast.extend(newscript)
                            return ast
                    return [scriptNode]
                else:
                    raise ParserError("script close expected", self.tokenizer.getLocationStr())
            else:
                raise ParserError("text expected", self.tokenizer.getLocationStr())
        else:
            raise ParserError("script expected", self.tokenizer.getLocationStr())
        
    # ScriptBlock --> ScriptOpen text-with-: ScriptClose DocBody ScriptOpen 'end' ScriptClose
    def parseScriptBlock(self, scriptNode):
        # the initial script node is already parsed and passed in
        something=self.parseDocBody(inBlock=True)
        if type(something) == types.TupleType:
            (body,script)=something
            if len(body)>=1:
                scriptNode.extend(body)
            return script
        else:
            raise ParserError("syntax error, script end tag missing?", self.tokenizer.getLocationStr())

    def processInstruction(self, instr, value, ast):
        value=value.strip()
        if instr=="include":
            if not stringInQuotes(value):
                raise ParserError("argument for include must be a quoted string",self.tokenizer.getLocationStr())
            value=value[1:-1]

            if value.startswith("http://") or value.startswith("HTTP://"):
                raise ParserError("included URLs must be local (relative to the page itself)")

            filename=os.path.join(self.fileLocation, value)
    
            try:
                (inputenc, outputenc) = determineInputOutputEncodings(filename)
                includeStream = self.openIncludedFile(filename, encoding=inputenc)
            except Exception,x:
                raise ParserError("error including file '%s': %s" % (value, x), self.tokenizer.getLocationStr())

            parsed=Parser(includeStream, filename, inputenc).parse()
            includeStream.close()
            # only add import declarations!!
            for item in parsed:
                if isinstance(item, Declaration):
                    if item.name=="import":
                        self.includedDeclarations.append(item)
                    elif item.name=="outputencoding":
                        self.checkUseChildEncoding(item.value)
            ast.append(Comment("BEGIN INCLUDE %s" % value ))
            ast.extend(parsed)
            ast.append(Comment("END INCLUDE %s" % value ))
        elif instr=="call":
            if not stringInQuotes(value):
                raise ParserError("argument for call must be a quoted string",self.tokenizer.getLocationStr())
            value=value[1:-1]
            ast.append(URLCall(value))
        elif instr=="redirect":
            if not stringInQuotes(value):
                raise ParserError("argument for redirect must be a quoted string",self.tokenizer.getLocationStr())
            value=value[1:-1]
            ast.append(URLForward(value))
        elif instr=="httpredirect":
            if not stringInQuotes(value):
                raise ParserError("argument for httpredirect must be a quoted string",self.tokenizer.getLocationStr())
            value=value[1:-1]
            ast.append(HTTPRedirect(value))
        elif instr=="insertpagebody":
            ast.append(InsertPageBody())
        else:
            raise ParserError("unknown instruction", self.tokenizer.getLocationStr())

    def checkUseChildEncoding(self, childenc):
        # check if we should use the child's encoding.
        for decl in self.declarations:
            if isinstance(decl, Declaration) and decl.name=="outputencoding":
                return  # we already have our own encoding, do not change it!
        # we don't have an encoding, use the child's encoding
        self.declarations.append( Declaration("outputencoding", childenc) )
        self.outputEncoding_fromChild = True
    
    def openIncludedFile(self, filename, encoding=None, raw=False):
        if raw:
            return file(filename,"rb")
        elif encoding:
            return codecs.open(filename, mode="rb", encoding=encoding)
        else:
            return file(filename, "r")


# test methods      
                
def syntaxTreeToStr(c):         # JUST FOR TESTING!! Not used by compiler.py
    s=""
    if isinstance(c, Document):
        for child in c:
            s+=syntaxTreeToStr(child)
    elif isinstance(c,  Declaration):
        s+="<%%@%s=%s@%%>" % (c.name, c.value)
    elif isinstance(c,URLCall):
        s+='\n----> CALL URL HERE: '+c.url+'\n'
    elif isinstance(c,URLForward):
        s+='\n----> REDIRECT URL HERE: '+c.url+'\n'
    elif isinstance(c,Comment):
        s+='\n# '+c.text+'\n'
    elif isinstance(c,TextBlock):
        if isinstance(c,Whitespace):
            s+='['+c.text+']'
        else:
            s+='{'+c.text+'}'
    elif isinstance(c, Expression):
        s+="<%%=%s%%>" % c.text
    elif isinstance(c, Script):
        s+="<%SCRIPTID:"+`id(c)`+"\t"+c.text+"%>"
        for child in c:
            s+=syntaxTreeToStr(child)
        s+="<%end SCRIPTID:"+`id(c)`+"%>"
    elif isinstance(c, InsertPageBody):
        s+="\n----> TEMPLATED PAGE BODY HERE\n"
    else:
        raise ValueError("invalid syntax "+repr(c))

    return s
    
def main(args):
    if len(args)>2:
        inputstream = codecs.open(args[1], mode="rb", encoding=args[2])
        print "Reading with input encoding ",args[2]
        inputenc = args[2]
    else:
        inputstream = open(args[1], "r")
        print "Reading with default encoding"
        inputenc=None

    parser = Parser(inputstream, args[1], inputenc)
    
    #decls = parser.parseDeclarationsOnly()
    #print "DECLS=",decls   # XXX
    
    syntaxtree=parser.parse()
    print syntaxtree
    print '*'*70
    
    string = syntaxTreeToStr(syntaxtree)
    if len(args)>2:
        print string.encode("iso-8859-1", "xmlcharrefreplace")
    else:
        print string


if __name__=="__main__":
    import sys
    main(sys.argv)
    
