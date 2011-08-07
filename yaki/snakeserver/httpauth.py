#############################################################################
#
#	$Id: httpauth.py,v 1.13 2008/10/12 15:42:16 irmen Exp $
#	HTTP authentication logic
#
#	This is part of "Snakelets" - Python Web Application Server
#	which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import sys, hashlib

class AuthError(Exception): pass
class WrongPassword(AuthError): pass

#
#   Perform HTTP authentication.
#    params:
#   request, response: snakelet request, response objects.
#   authorizeUserPasswordFunc: callback function func(method, url, username, passwd, request)
#       that must return True or False indicating if the user+passwd is correct.
#   authMethod: authentication method to use. "httpbasic" or "httpdigest"
#   authRealm: optional 'realm' string to use in the password dialog.
#
#   AUTH OK --> returns (authorized user name, password, set-of-privileges)
#   AUTH FAILED --> has prepared the response for HTTP authentication headers,
#           and raises AuthError
#
def HTTPauthenticate(request, response, url, authorizeUserPasswordFunc, authMethod="httpbasic", authRealm=None):

    def KD(secret, data):
        return hashlib.md5(secret + ":" + data).hexdigest()

    try:
        # first try and see if the browser sent us some authorization headers,
        # if so, process these to try to authorize the user.
        auth=request.getAuth() # 'Authorization' header from http request
        if not auth:
            raise AuthError('browser needs to supply authentication information for this URL')  # no auth provided.
        
        (scheme, digest) = auth.split(' ',1)
        if scheme.lower()=='basic':     # Basic authentication 
            try:
                (username, password)=digest.decode('base-64').split(':')
                try:
                    privileges = authorizeUserPasswordFunc("httpbasic", url, username, password, request)
                    if privileges is not None:
                        return username,password,privileges  # successful authentication!!!
                except Exception,x:
                    print >>sys.stderr, "error during passwd check:",x
                    # raise AuthError("error during passwd check: "+str(x))
                    raise
                raise WrongPassword('invalid username or password')
            except ValueError:
                raise AuthError('invalid digest string')

        elif scheme.lower()=='digest':
            # XXX due to the fact that we don't store plain passwords in Snakelets users,
            #     it is impossible to support digest auth. That requires access to plain passwords.
            #     The code below seems to work fine otherwise though.
            #raise AuthError('unsupported auth method: '+scheme) # not supported....
            digest=[d.strip() for d in digest.split(',')]
            dig={}
            for digestitem in digest:
                (name,value) = digestitem.split('=')
                if value.startswith('"') and value.endswith('"'):
                    value=value[1:-1]
                dig[name.lower()]=value
            username = dig['username']
            #password="password" # XXX should be gotten from from user database, but impossible: we don't store plain passwords
            if dig.get('algorithm') in (None, 'md5', 'MD5'):
                hA1=hashlib.md5( username+':'+dig['realm']+':'+ password).hexdigest()
            else:
                raise AuthError('unsupported algorithm: '+dig['algorithm'])
            if dig.get('qop') in (None, 'auth','Auth'):
                hA2=hashlib.md5(request.getMethod()+':'+dig['uri']).hexdigest()
            else:
                raise AuthError('unsupported QOP: '+dig['qop'])
            if dig['qop'].lower() == "auth":
                computed_request_digest = KD(hA1, dig['nonce']+':'+dig['nc']+':'+dig['cnonce']+':'+dig['qop']+':'+hA2 )
            else:
                computed_request_digest = KD(hA1, dig['nonce']+":"+hA2 )
            if computed_request_digest!=dig['response']:
                raise AuthError("Invalid Authentication") # invalid user/password/whatever...
            try:
                privileges = authorizeUserPasswordFunc("httpdigest", url, username, password, request)
                if privileges is not None:
                    return username,password,privileges # Successful authentication
            except Exception,x:
                print >>sys.stderr, "error during passwd check:",x
                # raise AuthError("error during passwd check: "+str(x))
                raise
            raise WrongPassword("Invalid Authentication") # invalid user/password/whatever...
        else:
            raise AuthError('unsupported auth method: '+scheme) # not supported....

    except AuthError,x:
        # Something went wrong with authenticating the user.
        # Send HTTP authentication headers.
        if authMethod=="httpbasic":         # Basic authentication
            name = authRealm or request.getWebApp().getName()[1] or "Web application"
            response.setHeader("WWW-Authenticate","Basic realm=\""+name+"\"")
            response.sendError(401) # AUTHORIZATION REQUIRED
            raise
        elif authMethod=="httpdigest":      # Digest authentication
            #response.sendError(501, "digest-auth not supported")
            #raise AuthError('digest-auth not supported') # not supported due to no access to plain passwords....
            realm = request.getWebApp().getName()[1] or "Web Application"
            nonce= hashlib.sha().hexdigest(str(time.time()) + "lamesecret")
            details = "Digest realm=\"%s\", nonce=\"%s\", algorithm=\"MD5\", qop=\"auth\"" % (realm, nonce)
            response.setHeader("WWW-Authenticate", details)
            response.sendError(401)    # AUTHORIZATION REQUIRED
            raise
        else:
            raise ValueError("unknown auth method "+authMethod)
