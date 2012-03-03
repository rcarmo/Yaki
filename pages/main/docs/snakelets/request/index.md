From: Rui Carmo
Date: 2012-03-03 23:03:00
Content-Type: text/x-markdown
Title: Request
Tags: snakelets, docs, draft

A request object provides all the information you need to handle HTTP requests in your snakelets' `serve` method, and has the following methods:

### `getServerSoftware()` ###
Returns the server software version (`string`).

### `getSnakeletsVersion()`### 
Returns the Snakelets version (`string`).

### `getServerIP()` ###
Returns the server IP address (`string`).

### `getServerName()` ###
Returns the virtual host to which the request is being addressed (`string`).

### `getRealServerName()` ###
Returns the real (internal) server hostname (`string`).
 
### `getServerProtocol()` ###
Returns the HTTP protocol (i.e.. `HTTP/1.0`) in use (`string`).
 
### `getServerPort()` ###
Returns the HTTP port in use (`integer`).

### `getRequestURL()` ###
Returns the URL path and query string (i.e., `/page/test.cgi?arg=34`) (`string`). 
Use with the `getBaseURL` method to assemble a complete URL.  

### `getRequestURLplain()` ###
Like `getRequestURL`, but also without any query args. 
Use with the `getBaseURL` method to assemble a complete URL without query args.
 
### `getBaseURL()` ###
The base URL of the server (`string`)
Example: `http://desertfish.xs4all.nl:9080`

### `getPathInfo()` ###
Any additional URL path components after the snakelet URL (`string`).
Example: for `snoop.sn/foo/bar?arg=value`, it returns `/foo/bar`. 
<small>Note: this is always empty when you use a `fnmatch` URL pattern for your snakelet, and this string is not url-escaped.</small>

### `getMethod()` ###
The HTTP method (`GET` or `POST`) used (`string`).

### `getQuery()` ###
The query args of the URL (`string`).
Example: `arg=value&amp;name=foo%21` (this string is url-escaped)

### `getFullQueryArgs()` ###
All the query args including path info (`string`).
Example: `/zip/zap?delete&amp;arg=value&amp;name=foo%21` 
<small>Note: this is not the full URL, and this string is url-escaped.</small>

### `getRemoteHost()` ###
Remote hostname (`string`).

### `getRemoteAddr()` ###
Remote host IP (`string`).
 
### `getRealRemoteAddr()` ###
The 'real' IP address of the remote host (`string`).
Extracted from any `X-Forwarded-For` headers inserted by reverse proxies.

### `getContentType()` ###
The `Content-type` header of the request (`string`).

### `getContentLength()` ###  
Content length of the request (`int`).

### `getUserAgent()` ###
Browser user agent or '' (`string`).

### `getReferer()` ###
the referring URL (that is: the url the client request came from), or '' (empty string)

### `getCookie()` ###
raw cookie information, as a comma separated string

### `getCookies()` ###
parsed cookies (`mycookie.SimpleRequestCookie` object - a `dict` mapping cookie names to a `list` of string values)


### `clearCookies()` ###
erases all cookie information from the request (not from the client!)

### `getInput()` ###
request input stream (socket/file)
 
### `getArg()` ###
URL argument. Example: when `url=snoop.sn?command&arg=name` it returns `command` (this string is _not_ url-escaped)

### `setArg(arg)` ###
reset the URL argument (`getArg()`) to something new.

### `getWebApp()` ###
the current WebApp object

### `getRangeStr()` ###
the unparsed string value of the HTTP `Range` header, or '' (empty string).

### `getRange()` ###
the parsed HTTP `Range` header, as a tuple: (from,to)

### `getAuth()` ###
the HTTP `Authorization` header value, or '' (empty string).

### `getAllHeaders()` ###
all HTTP headers (`mimetools.Message` object)

### `getHeader(header)` ###
value of specified HTTP header, or None if it isn't present

### `getForm()` ###
parsed form contents (a `dict`, as in `{paramname: value}` ) The form has an `urlencode()` utility method that returns an url-encoded query args string like `arg=value&foo=bar` for the form's parameters.
 
### `getField(param, default='')` ###
value of a single form field parameter (or the provided default value - which is an empty string if not otherwise given - if the parameter doesn't exist)
 
### `getParameter(param, default='')` ###
value of a single form field or request context parameter (or the provided default value - which is an empty string if not otherwise given - if the parameter doesn't exist).
The request form is first examined - if it does not contain the required field, the request context is examined for a matching attribute. If it too does not have it, the default is returned.

### `getContext()` ###
Request context (`ContextContainer` object). Scope: request.
Unique per user and per request, destroyed after request completes.

### `getSession()` ###
The session object (`snakeserver.snakelet.Session` object), `None` if there is no session

### `deleteSession()` ###
Logout current user and deletes the session object. Also clears all cookie info on the request (not on the client!)

### `getSessionContext()` ###
The session context (`ContextContainer` object). 
Scope: session. Unique per user, shared for all requests of this user. None if there is no session.

### `getMaxPOSTsize()` ###
The current max size of a `POST` request (in bytes)

### `setMaxPOSTsize(numbytes)` ###
Set the maximum size in bytes of a `POST` request (default: 200KB). If it is larger, the server aborts the connection and the `POST` request fails, and a `FormFileUploadError` exception is raised.

### `getEncoding()` ###
The current request character encoding. `None` if not specified (means default).

### `setEncoding(encoding)` ###
Forces the request character encoding. This is often necessary to correctly read non-ASCII characters from form `POST`. Also note that returned form fields will be unicode objects (instead of regular strings) if you set the encoding.
If you try to change the encoding after the request form fields have already been accessed, `ValueError` will be raised. Using this method will override any default `RequestEncoding` that may be defined on the webapp.

Getting request parameters is done using `getForm()`, or `getParameter()`. You can clear all parameters for the duration of the request using `getForm().clear()` (since it is a `dict`).

If you need to add or modify request parameters from inside your code, you should update the appropriate keys in the `dict` object returned from `getForm()`.