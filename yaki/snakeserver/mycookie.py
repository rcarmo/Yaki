#############################################################################
#
#	$Id: mycookie.py,v 1.11 2005/04/23 00:48:37 irmen Exp $
#	Custom HTTP-cookie code
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

from Cookie import *
from Cookie import Morsel, _unquote, _quote, _CookiePattern
import types

# irmen: ripped from standard lib's Cookie
# I had to have a way of detecting multiple cookies with
# the same name. Standard cookie lib can't do that.
#
# NOTE: THIS COOKIE IMPLEMENTATION IS ONLY FIT FOR PARSING
#       COOKIES ON INCOMING REQUESTS! IT CANNOT BE USED FOR
#       CREATING COOKIES ON OUTGOING REPLIES!
#

# Also, here the magic cookie name for the session id is defined:

SESSION_COOKIE_NAME = "SNSESSID"
SESSION_COOKIE_NAME_SHARED = "SNSESSIDSHR"



class SimpleRequestCookie(dict):

    def __init__(self, input=None):
        self.mydict={}
        if input: self.load(input)

    def value_decode(self, val):
        return _unquote( val ), val
    def value_encode(self, val):
        strval = str(val)
        return strval, _quote( strval )


    def __set(self, key, real_value, coded_value):
        # Store only the real_value.
        # Can store duplicate cookies because we're using a list.
        dict.setdefault(self, key, []).append(real_value)

    def __setitem__(self, key, value):
        rval, cval = self.value_encode(value)
        self.__set(key, rval, cval)

    def load(self, rawdata):
        """Load cookies from a string (presumably HTTP_COOKIE) or
        from a dictionary.  Loading cookies from a dictionary 'd'
        is equivalent to calling:
            map(Cookie.__setitem__, d.keys(), d.values())
        """
        if type(rawdata) in types.StringTypes:
            self.__ParseString(rawdata)
        else:
            self.update(rawdata)
        return

    def __ParseString(self, strng, patt=_CookiePattern):
        i = 0            # Our starting point
        n = len(strng)     # Length of string
        M = None         # current morsel

        while 0 <= i < n:
            # Start looking for a cookie
            match = patt.search(strng, i)
            if not match: break          # No more cookies

            K,V = match.group("key"), match.group("val")
            i = match.end(0)

            # Parse the key, value in case it's metainfo
            if K[0] == "$":
                # We ignore attributes which pertain to the cookie
                # mechanism as a whole.  See RFC 2109.
                # (Does anyone care?)
                continue
            elif K.lower() in Morsel._reserved:
                continue
            else:
                rval, cval = self.value_decode(V)
                self.__set(K, rval, cval)
                M = self[K]
