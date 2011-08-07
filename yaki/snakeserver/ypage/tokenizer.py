#############################################################################
#
#	$Id: tokenizer.py,v 1.26 2006/06/04 11:35:07 irmen Exp $
#	Ypage tokenizer
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

#
#   This tokenizer uses an intelligent character stream reader to
#   chop up the input stream (the ypage file) into lexical tokens such as 
#   'the start of a script block', 'the end of a declaration' etc.
#   Because the tokenizer is a python generator, it produces tokens
#   one-by-one in a memory friendly way.
#

from __future__ import generators
import types
import weakref

class TokenizerError(Exception):
    def __init__(self, tokenizer, msg):
        if tokenizer:
            msg = msg+" @"+str(tokenizer.getLocationStr())
        Exception.__init__(self, unicode(msg).encode("unicode-escape") )

UTF8_BOM=u'\ufeff'
UTF8_BOM_ENCODED=UTF8_BOM.encode("UTF-8")

# special token IDs
TOK_DECLARATIONOPEN   = 1000
TOK_EXPRESSIONOPEN    = 1001
TOK_SCRIPTOPEN        = 1002
TOK_SCRIPTCLOSE       = 1003
TOK_SCRIPTCLOSEKEEPB  = 1004
TOK_COMMENTOPEN       = 1005
TOK_COMMENTCLOSE      = 1006
TOK_INSTRUCTIONOPEN   = 1007

# stream reader that can peek ahead and unread a character
class BufferedChars(object):
    def __init__(self, tokenizerref, stream):
        self.stream=stream
        self.chars=[]
        self.nextIdx=0
        self.tokenizerref=tokenizerref
        self.previousChar=None
        self.linenumber=0
        # handle the UTF-8 BOM, if present
        x=self.next()
        if type(x) is unicode:
            if x==UTF8_BOM:
                pass  # skip the UTF-8 BOM.
            else:
                # it was a different unicode character. Put it back.
                self.unread()
        elif x=='\n':
            self.unread() # no BOM
        else:
            # there could still be a BOM at the beginning, but the input
            # file is not read in Unicode. Find out if this is the case,
            # if so, abort with appropriate error.
            x+=self.next()
            if x.endswith('\n'):  # no BOM
                self.unread()
                self.unread()
            else:
                x+=self.next()
                if x==UTF8_BOM_ENCODED:
                    raise TokenizerError(None,"file has UTF-8 BOM, but the page compiler has not set the right inputencoding (UTF-8)")
                else:
                    self.unread()
                    self.unread()
                    self.unread()

        
    def next(self):
        try:
            self.previousChar = self.chars[self.nextIdx-1]
            self.nextIdx+=1
            return self.chars[self.nextIdx-1]
        except IndexError:
            self.linenumber+=1
            if self.chars:
                self.previousChar = self.chars[-1]
            self.chars=self.stream.readline()
            if self.chars:
                if self.chars.endswith('\r'):
                    self.chars+='\n' # work-around for Python 2.4.1 codecs.readline bug (SF #1175396)
                self.nextIdx=1
                return self.chars[0]
            else:
                # end of stream
                self.nextIdx=-1
                return None

    def peek(self):
        return self.chars[self.nextIdx]
        
    def previous(self):
        return self.previousChar
        #if self.nextIdx>=2:
        #   return self.chars[self.nextIdx-2]
        #else:
        #   raise TokenizerError(self.tokenizerref(), "cannot return last char: buffer empty")

    def unread(self):
        self.nextIdx-=1
        if self.nextIdx<0:
            raise TokenizerError(self.tokenizerref(), "cannot unread char: buffer empty")

    def getLineNumber(self):
        return self.linenumber
    def getColumn(self):
        return self.nextIdx
        
            
# Stream tokenizer (using generators so memory friendly)
class Tokenizer(object):
    def __init__(self, stream, filename):
        self.chars=BufferedChars(weakref.ref(self), stream)
        self.filename=filename
        
    def getLocationStr(self):
        return "line %d col %d (file: %s)" % self.getLocation()
    def getLocation(self):
        return self.chars.getLineNumber(), self.chars.getColumn(), self.filename
        
    def getTokens(self):            # a generator!
        buf=[]
        while True:
            c= self.chars.next()
            if not c:
                break
            elif c=='<' and self.chars.peek()=='%':
                # <% open tag. First yield the buffer that we have accumulated until now.
                if buf:
                    yield ''.join(buf)
                    buf=[]
                self.chars.next()
                next=self.chars.peek()
                if next=='@':
                    self.chars.next()
                    yield TOK_DECLARATIONOPEN
                elif next=='$':
                    self.chars.next()
                    yield TOK_INSTRUCTIONOPEN
                elif next=='=':
                    self.chars.next()
                    yield TOK_EXPRESSIONOPEN
                elif next=='!':
                    # could be a comment <%!--
                    self.chars.next()
                    if self.chars.next()=='-':
                        if self.chars.next()=='-':
                            yield TOK_COMMENTOPEN
                            continue
                        self.chars.unread()
                    self.chars.unread()
                    # hm, it is not <%!--, just a script.
                    yield TOK_SCRIPTOPEN
                else:
                    yield TOK_SCRIPTOPEN
            elif c=='-' and self.chars.peek()=='%':
                # could be comment close: --%>
                if self.chars.previous()=='-':
                    self.chars.next() # skip the %
                    if self.chars.peek()=='>':
                        self.chars.next()
                        # yield the buffer upto the previous char
                        if len(buf)>1:
                            yield ''.join(buf[:-1])
                        buf=[]
                        yield TOK_COMMENTCLOSE
                        continue
                    else:
                        self.chars.unread() # rollback the %
                # it's a normal '-', append it
                buf.append('-') 
            elif c=='%' and self.chars.peek()=='>':
                if self.chars.previous()=='\\':
                    # it's a \%> close tag
                    tag = TOK_SCRIPTCLOSEKEEPB
                    del buf[-1] # get rid of the \
                else:
                    tag = TOK_SCRIPTCLOSE
                # %> close tag.
                if buf:
                    yield ''.join(buf)
                    buf=[]
                self.chars.next() # read the '>'
                yield tag

            else:
                # add the char to the buffer
                if c=='\n' and self.chars.previous()=='\r':
                    buf[-1]='\n'   # replace \r\n by \n
                else:
                    buf.append(c)
                
        # yield the remaining buffer, if any.
        if buf:
            yield ''.join(buf)
            buf=[]




# test method
                
def main2(args):
    tok = Tokenizer(open(args[1], "r"), args[1])
    for t in tok.getTokens():
        print `t`

def main(args):
    if len(args)>2:
        import codecs
        inputstream = codecs.open(args[1], mode="rb", encoding=args[2])
        print "Reading with input encoding ",args[2]
    else:
        inputstream = open(args[1], "r")
        print "Reading with default encoding"
    tok = Tokenizer(inputstream, args[1])
    s=""
    for t in tok.getTokens():
        if t==TOK_DECLARATIONOPEN:
            s+="<%@"
        elif t==TOK_INSTRUCTIONOPEN:
            s+="<%$"
        elif t==TOK_EXPRESSIONOPEN:
            s+="<%="
        elif t==TOK_SCRIPTOPEN:
            s+="<%"
        elif t==TOK_SCRIPTCLOSE:
            s+="%>"
        elif t==TOK_SCRIPTCLOSEKEEPB:
            s+="\\%>"
        elif t==TOK_COMMENTOPEN:
            s+="<%!--"
        elif t==TOK_COMMENTCLOSE:
            s+="--%>"
        elif type(t) in types.StringTypes:
            s+="{"+t+"}"
        else:
            raise ValueError("invalid token "+repr(t))
    print '*'*70
    
    if len(args)>2:
        print s.encode("ISO-8859-1", "xmlcharrefreplace")
    else:
        print s


if __name__=="__main__":
    import sys
    main(sys.argv)
