## Setting up a web application ##

A web application is a [Python][p] module in the `webapps` directory. The directory (module) name is also the name and URL context name of your web application - so when your web app is in a directory called `store`, it will be accessible with under the URL tree starting with `/store`. 

There is one reserved name: if you have a web app named `ROOT`, that will be the default application, handling URL context `/`. (When you are using Virtual Hosting settings, you can change this, it is only used when no vhosts are defined).

> If you're used to other web app framework conventions for URL handling, you can think of Snakelets as using webapp/module names as basic routes - but you can handle sub-routes (or `ROOT` routes) in Snakelets handlers, or assign them separately in virtual hosts.

The module's `__init__.py` must contain the configuration settings for your web app. Here's a simple example:

<pre src="__init__.py.1.txt" syntax="python"></pre>

There are, however, plenty more settings, which are detailed in the following sections:

## Attributes ##

### `name` ###

The descriptive name for this webapp.

### `docroot` ###

The (relative) directory where files are served from, usually `.` (which means the directory of the webapp itself).

The convention is to use `docroot` or `web` here and place static files and Ypages inside to isolate those from your application code.

### `assetLocation` ###

The (relative or absolute) url location where static assets are to be found, as used by the `asset` Ypage function and the `mkAssetURL` Webapp method.

* If you store your assets inside the webapp's `docroot`, you should use a relative location (i.e., `static/img/` or `.` to use the `docroot` itself).

* If you share assets among webapps (or even store them in another server), you should use an absolute path (i.e., `/static/img/` or `http://imagefarm/static/img/`).
    
### `snakelets` ###

A dictionary that maps (relative) URL patterns to snakelet classes (analogous to routes in other frameworks).

<pre src="__init__.py.2.txt" syntax="python"></pre>

If you use wildcards, however, you lose the ability to use _path info_ (i.e., `http://.../docs/report.pdf/path/info?foo=bar` doesn't work, but `http://.../docs/report.pdf?foo=bar` still does).

<!-- TODO: <br/>See below how you can use Snakelets as virtual <a href="#indexpages_title">index pages</a> -->

### `configItems` ###

The app-specific configuration items that are made available through `getConfigItem()`.

### `sessionTimeoutSecs` ###

The user session timeout (defaults to 600s/10 minutes).

### `sessionTimeoutPage` ###

A relative URL for a page shown when the user session times out (the default Snakelets behavior is to try to create a new session without notice).

### `sharedSession` ###

A boolean value (defaulting to `False`) that indicates if the app uses a global shared session (i.e., valid throughout the Snakelets instance to all apps that wish to use it).

This allows for shared sign-on among applications as well, since the logged in user object is also shared.

### `sharedSessionTLD` ###

Cookie domain to use for shared session cookies. Useful when the same webapp is available on multiple virtual hosts (`xx.domain.tld` and `yy.domain.tld`) and you want to share sessions among these subdomains.
    
### `defaultRequestEncoding` ###

Default encoding used when reading incoming request data (such as form POSTs). Defaults to your [Python][p] environment's default encoding, and can be overriden via `request.setEncoding()`.

### `defaultOutputEncoding` ###

Default encoding used for Ypage/snakelet output.

### `defaultContentType` ###

Specify the content type of dynamic pages (defaults to `text/html`).

### `defaultPageTemplate` ###

Specify the default page template file to use for formatting Ypages without an explicit page template declaration (defaults to `None`).

### `defaultErrorPage` ###

Specify the default errorpage to use for formatting server error pages.

<a name="indexpages"></a>    
### `indexPages` ###

      Setting this value allows you to use a custom 'index pages' list on a site-by-site basis.
It will override the default list of index pages that Snakelets looks for. If you don't specify it, the
default list is used. The built-in default list is `index.y, index.html, index.htm` (in this order).
Only real files can be mentioned in this list. It is possible to use Snakelets as <a href="#indexpages_title">'virtual' index pages</a> but that is configured elsewhere.

    
## Functions ##

### `def dirListAllower(path): ...` ###

Implement this function to filter requests for directory listings for `path` (where `path` is relative to the web app), regardless of user authorization. Return `True` to allow directory listings for a specific `path` (defaults to `False`).

### `def documentAllower(path): ...` ###

Implement this function to allow serving the given document (where `path` is relative to the web app), regardless of user authorization. Return `True` if allowed. By default, all documents are allowed except [Python][p] (`.py`) source files.

### `authorizationPatterns` ###

A dictionary that maps (relative) URL patterns to lists of privilege names that are allowed to access those URLs. <em>Note that the full URL must match the pattern before authorization is required, so Snakelets automatically appends the *-wildcard to the end of your pattern to avoid security holes. (Also: the server-wide url prefix is automatically prepended to your patterns)</em> See <a href=
        "authorization.html">authorization</a>. Default: all URLs are allowed (no privilege checks).
    
    
### `authenticationMethod` ###

A tuple (method, argument) that defines the user authentication method to use for the webapp. See [authorization][auth] (not defined by default, and overridable in snakelet methods or Ypages).

### `def authorizeUser(method, url, user, passwd, request): ...` ### 

An authorization handler you must implement if let Snakelets perform user authentication, and which is responsible for username/password validation. See [authorization][auth]. 

### `def init(webapp): ...` ###

An (optional) initializer for your web app, invoked before any snakelet class is initialized.

> *Note:* when deploying a web app on multiple vhosts, this is invoked once per vhost.

### `def close(webapp)...` ###

An (optional) destructor for your web app.
    
