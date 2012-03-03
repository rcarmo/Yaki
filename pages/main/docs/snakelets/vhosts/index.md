From: Rui Carmo
Date: 2012-03-03 23:10:00
Content-Type: text/x-markdown
Title: Virtual Hosts
Tags: snakelets, docs, draft

To make your web application available on multiple hosts, you have to add it to the virtual host configuration file. 

> See [Starting the Server](docs/snakelets/Starting)

## Python module/package names ##

There is a big catch concerning the naming of your packages and modules in the web apps (for instance, the package where your snakelets are in, or the name(s) of the modules that contain your snakelets). <em>They are not unique over all web applications (because every webapp's directory is placed in Python's module search path)!</em> This means that you cannot have a module or package called `snakelets` in one webapp and also a module or package with that name in another web application. This also means that your code is not protected from (ab)use by another web application. <em>This will very likely not be fixed, so keep this in mind!</em>

## Shared modules/libraries ##

Place modules and packages that you want to easily share between webapps in the `userlibs` directory.

### Create pages for the web application ###

Let's say that you have created a web application `testapp` and that it has a `docroot` directory where you will put your page files, so you must point the docroot attribute to it in the webapp's init file, as described above. The files in that directory will now be accessible in your browser by using the url `http://server.com/testapp/`

The index page of the webapp will be shown if you type `http://server.com/testapp/` or `http://server.com/testapp` in your browser - the trailing slash is not really required; you will be redirected to a correct url if it is missing (except when there is a page in the root webapp with the same name, in this case the page is loaded and you will not be redirected).

Snakelets maps the rest of the URL to the filesystem (=the contents of the docroot directory) in a rather straightforward way, much the same as a normal web server such as Apache does this. A path component in the url maps to a directory on disk, and a file component usually maps to a file on disk. So that means that when the url <strong>http://server.com/testapp/office/page.html</strong> is requested, Snakelets will return the `page.html` file from the `office` directory in the docroot location. For Ypages it is the same, <strong>http://server.com/testapp/office/login.y </strong>will cause Snakelets to load and run the `login.y` ypage in the given location. </p>
<p>It is <em>impossible</em> to request files outside the docroot location this way. That is nice, because you can protect your other files (web app source code and such) very easily just by placing them in a different directory as your web pages. You could fool around with the documentAllower function but this is more convenient and faster.</p>
<p>There is a big exception to the simple URL-to-filesystem mapping: <em><a href="snakelet.html">Snakelets</a>. </em>Dynamic content created by a snakelet page is not found on disk in the regular way. Instead, there is a <em>snakelet</em> object defined in your Python source code that is called by the server when a URL is requested that triggers the snakelet. Which URLs trigger which snakelets, is configured in the `snakelets` attribute in your webapp init file (see above). Because you can use simple wildcard patterns there, a lot of URLs may be mapped onto a single snakelet object. </p>
<p>The server uses the following order to determine what is returned for a requested URL:</p>
<ol>
  <li>Snakelet url/patterns</li>
  <li>Dynamic page (Ypage)</li>
  <li>Static page/file (.html etc) </li>
</ol>
<h4><a name="indexpages_title"><strong>Index pages</strong></a></h4>
<p>When you leave out a specific page name from an url (example: `http://server.com/app/info/`)
the server will try to fetch the <em>index page</em> for that directory.
If there is a file `index.html` (or `index.y`) in that location, Snakelets
will load that one. It is as if you typed the url `http://server.com/app/info/index.y`.
<br/>
See <a href="#indexpages">above</a> at the `indexPages` variable what the default list of
files is that are searched for, and how you can change this.</p>
<p>Snakelet as index page: if no other suitable page is found, the server will also try to use a Snakelet as index page.
You have to configure a snakelet with a suitable URL pattern to make this work.
The server looks for `index.sn` Snakelet in the requested URL path, so
when the URL `http://server.com/test/dir/` is requested and you have configured
a snakelet in the `test` webapp on the pattern `dir/index.sn` or `*/index.sn`
it will be used as index page. You can also use a Snakelet as 'root' index page in your webapp,
but you will have to add it explicitly to the Snakelet list (because of the way the fnmatch
urlpatterns work): use the pattern `index.sn` (no pre- or suffixes).
<br/>To avoid conflicts with other snakelets, <em>it is required</em> that the url pattern for your index snakelet(s)
explicitly ends in '`index.sn`'.
<br/><em>Note that you can create 'fake' directories using index Snakelets;</em> the directory that you use in
the snakelet url path pattern doesn't have to exist on disk - in contrast to regular index pages.</p>

<h4><strong>Smart Suffix Search </strong></h4>
<p>Snakelets also uses a 'smart suffix search'. This means that it is not strictly required to have the correct file suffix in the URL. This allows for 'cleaner' URLs.
If a page is not found, Snakelets will try again by -internally- appending the `.y`, `.html` and `.htm` suffixes (in that order).
 For instance, <strong>http://server.com/testapp/office/login.y</strong> will load the `login.y` Ypage, but so will <strong>http://server.com/testapp/office/login </strong>(the same url but without the .y suffix). 
 Notice that dynamic content has higher priority than static content, so if `login.y` and `login.html` both exist, the server will use `login.y`. This mechanism is rather useful when you are setting up a website: you can start with all static .html pages, and replace them later on with dynamic .y pages - without changing any of your URLs. </p>
<p>There is one small issue: the 'smart suffix search' does not work if you are using path components in the URL query parameters. For instance, <strong>http://server.com/testapp/office/login.y/floor1 </strong>will work (it will call login.y with `/floor1` pathinfo on the <a href="request.html">request</a>), but <strong>http://server.com/testapp/office/login/floor1 </strong>will <em>not</em> work.
(If you want something like this to work, use a Snakelet with a suitable URL pattern).
Note that regular query parameters <em>do</em> work: <strong>http://server.com/testapp/office/login?floor=1 </strong>works fine (it will call login.y with correct query parameters). </p>
<p>Smart suffixes and authorization patterns: when checking authorization patterns, Snakelets takes smart suffixes into account.
For more info see <a href="authorization.html">authorization</a>.</p>
<h4><strong>Automatic reloading</strong></h4>
<p>For fast development, Snakelets supports automatic page reloading. This means that when you update
an Ypage source file, or a Snakelets module source file, the server will detect that it has been updated
and it will reload and recompile the new version. This happens on-the-fly so you will directly see
the changes you have made in your browser.</p>
<p>To avoid problems and performance issues, the automatic reloading is limited to the Ypage source file
(and templates, if any) and the snakelet module file. Imported modules are <em>not</em> reloaded.
</p>

#### Directory Listings ####

[Snakelets][s] will show a listing of the contents of a directory if you navigate to it in the browser.

By default this funcion is disabled. Enable it by using an appropriate `dirListAllower` function in the webapp init file.

You can supply a special `.snindex` file inside the directory to add extra information to the directory listing.

It is a file with two configuration sections like so:

<pre syntax="ini">
[hidden]
.svn=

[filedescriptions]
file.txt=Just a text file
</pre>

In the `hidden` section you put all names that you don't want to show up in the listing (mind the '='!).
In the `filedescriptions` section you put all names with a comment text that you want to be shown in that entry's comment column in the listing.

[auth]: docs/snakelets/authorization
[s]: docs/snakelets
