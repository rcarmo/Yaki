## Request Object ##

A request object provides all the information you need to handle HTTP requests in your snakelets' `serve` method.

### `getServerSoftware()` ###

Returns the server software version as a string.


### `getSnakeletsVersion()`### 

Returns the snakelets version as a string.

### `getServerIP()` ###

Returns the server IP address as a string.

### `getServerName()` ###

Returns the virtual host to which the request is being addressed as a string.

### `getRealServerName()` ###

Returns the real (internal) server hostname as a string.
 
### `getServerProtocol()` ###

Returns the HTTP protocol in use (i.e.. `HTTP/1.0`) as a string.
 
### `getServerPort()` ###

Returns the HTTP port in use as an integer.

### `getRequestURL()` ###

Returns the URL path and query string (i.e., `/page/test.cgi?arg=34`) as a string. Use with the `getBaseURL` method to assemble a complete URL.  
 
### `getRequestURLplain()` ###

like `getRequestURL`, but also without any query args. Use with the next method (`getBaseURL`) to obtain a complete URL without query args.
 
### `getBaseURL()` ###
the base URL of the server. Example: `http://desertfish.xs4all.nl:9080`

### `getPathInfo()` ###
any additional URL path components after the snakelet URL. Example: when url is `snoop.sn/foo/bar?arg=value`, it returns `/foo/bar`. (Note: this is always empty when you use a `fnmatch` URL pattern for your snakelet!) (this string is <em>not</em> url-escaped)
 
### `getMethod()` ###
the HTTP method used (`GET` or `POST`)

### `getQuery()` ###
the query args of the URL, example: `arg=value&amp;name=foo%21`. (this string <em>is still</em> url-escaped)
 
### `getFullQueryArgs()` ###
all the query args including path info and command, example: `/zip/zap?delete&amp;arg=value&amp;name=foo%21` (note: this is not the full URL! You can get that one from the Snakelet) (this string <em>is still</em> url-escaped)

### `getRemoteHost()` ###
hostname of the remote host (string)

### `getRemoteAddr()` ###
IP address of the remote host (string)
 
### `getRealRemoteAddr()` ###
the 'real' IP address of the remote host (use this if you are running behind a reverse proxy)

### `getContentType()` ###
the content-type of the request (string)

getContentLength()
content length of the request (int)
 
 
getUserAgent()
browser ID string of the client's browser, or '' (empty string)
 
 
getReferer()
the referring URL (that is: the url we came from), or '' (empty string)
 
 
getCookie()
raw cookie information (comma separated string)
 
 
getCookies()
parsed cookies (mycookie.SimpleRequestCookie object, this is a dict, which maps cookie names to a <em>list</em> of string values)
 
 
clearCookies()
erases all cookie information from the request (not from the client!)
 
 
getInput()
request input stream (socket/file)
 
 
getArg()
URL argument. Example: when url=snoop.sn?command&amp;arg=name it returns `command` (this string is <em>not</em> url-escaped)
 
 
setArg(arg)
reset the URL argument (getArg() ) to something new.
 
 
getWebApp()
the current WebApp object
 
 
getRangeStr()
the unparsed string value of the HTTP 'range' header, or '' (empty string).
 
 
getRange()
the parsed HTTP 'range' header; a tuple: (from,to)
 
 
getAuth()
the HTTP Authorization header value, or '' (empty string).
 
 
getAllHeaders()
all HTTP headers (mimetools.Message object)
 
 
getHeader(header)
value of specified HTTP header, or None if it isn't present
 
 
getForm()
parsed form contents (a dict of {param name: value} ) The form has a utility method <code>urlencode()</code> that returns an url-encoded query args string like `arg=value&amp;foo=bar` for the form's parameters.
 
 
getField(param, default='')
value of a single form field parameter (or the provided default value -which is an empty string if not otherwise given- if the parameter doesn't exist)
 
 
getParameter(param, default='')
value of a single form field or request context parameter (or the provided default value -which is an empty string if not otherwise given- if the parameter doesn't exist). 
  The request form is first examined, if it does not contain the required field, the request context is examined for a matching attribute. If it too does not have it, the default is returned.
 
 
getContext()
request context (ContextContainer object). Scope: request. <em>unique per user and per request, destroyed after request completes</em>
 
 
getSession()
the session object (snakeserver.snakelet.Session object), None if there is no session
 
 
deleteSession()
logout current user and deletes the session object. Also clears all cookie info on the request (not on the client!)
 
 
getSessionContext()
the session context (ContextContainer object). Scope: session. <em>unique per user, shared for all requests of this user.</em> None if there is no session.
 
 
getMaxPOSTsize()
the current max size of a POST request (in bytes)
 
 
setMaxPOSTsize(numbytes)
set the maximum size in bytes of a POST request (default: 200000=200Kb). If it is larger, the server aborts the connection and the POST request fails, and a FormFileUploadError exception is raised.
 
 
getEncoding()
the current request character encoding. None if not specified (means default).
 
 
setEncoding(encoding)
forces the request character encoding. This is often necessary to correctly read non-ASCII characters from From Posts. Also note that returned form fields will be unicode objects (instead of regular strings) if you set the encoding.
  If you try to change the encoding after the request form fields have already been accessed, a ValueError will be raised.
  Using this method will override a defaultRequestEncoding that may be defined on the webapp.

<p>Getting request parameters is done using <code>getForm()</code>, or <code>getParameter()</code>. You can clear all parameters for the duration of the reqeuest using <code>getForm().clear()</code> (because it is just a dict).
 If you need to add or modify request parameters from inside your code, you should update the appropriate keys in the dict object
 that is returned from <code>getForm()</code>.</p>