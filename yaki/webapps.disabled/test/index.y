<%@session=yes%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
	<title>Snakelets Server test pages</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">
<!--
body,td,th {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 10pt;
	color: #000000;
}
body {
	background-color: #EEFFFF;
}
h1 { font-size: 14pt; }
h2 { font-size: 12pt; }
-->
</style></head>
<body>
	<h1>Welcome to the Snakelets Server test pages.</h1>
    <h2>Various</h2>
    <ul>
      <li><strong><a href="snoop.sn">Snoop a request</a></strong>. &nbsp;</li>
      <li>View memory usage: <a href="memory.sn">[snakelet]</a> / <a href="memory.y">[ypage]</a>
</li>
      <li><a href="testform.y">Test form</a>.</li>
      <li><a href="urlasset.y">Demo of url() and asset()</a>.</li>
      <li><a href="fake/">Fake directory index page.</a></li>
    </ul>
    <p><em>This Web App's configuration file and snakelet directory. Usually you're not allowed to see these files but this web app has more relaxed document allower functions so you can view the </em>
    <a href="__init__.py">Config file</a> <em>and also browse into the</em> <a href="tsnakelets/">Snakelets source directory</a>. </p>
    <h2>Cookies</h2>
    <p>Testing for cookies: <a href="cookie.sn">in a Snakelet</a>, <a href="cookie.y">in an Ypage (preferred!)</a>, <a href="cookiejs.y">with Javascript</a>
<h2>Redirect/include</h2>
    <ul>
      <li><a href="redirect.sn">Redirection / inclusion in snakelet</a>.</li>
      <li><a href="includetest.y">$include in ypage</a>. </li>
      <li><a href="encoding.y">Character encodings</a>.</li>
      <li><a href="utf8form/">UTF-8 Form submits.</a></li>
    </ul>
    <h2>Error page </h2>
    <ul>
      <li><a href="testerror_cust.y">Custom error page</a>.
    (<a href="testerror_norm.y">Normal error page</a>).</li>
      <li> <a href="error.sn?custom=true">Custom error snakelet</a>.
      (<a href="error.sn">Normal error snakelet</a>). </li>
    </ul>
    <h2>Page templates and inheritance </h2>
    <ul>
      <li><a href="inherit.y">Page inheritance.</a> </li>
      <li><a href="templatepage1.y">Templated page 1</a>, <a href="templatepage2.y">Templated page 2</a>.</li>
      <li> <a href="templatepage_error.y">Templated page with custom errorpage</a>.</li>
    </ul>
    <h2>HTTP authentication </h2>
    <p><em>Recognised users are 'mike' with password 'apples', and 'janet' with password 'pookie'; mike has admin/dba rights, while janet is a secretary</em>    
    <ul>
      <li><a href="auth/mgmt/httpauth.sn">Authenticate for realm &quot;Management&quot;.</a></li>
      <li> <a href="auth/bo/httpauth.sn">Authenticate for realm &quot;Backoffice&quot;.</a></li>
      <li>        <a href="testauth.y">HTTP auth in an Ypage</a> (try both);
        <a href="authpattern.y">auth using authpatterns</a> (needs admin)
        (<a href="authpattern">should also work with smart suffix search</a>)
      </li>
    </ul>
    <h2>Shared Sessions </h2>
<p>The following two webapps have a <em>shared session</em>, which allows them to share a single user logon:
<ul>
<li><a href="../shared1/">Shared #1</a>
<li><a href="../shared2/">Shared #2</a>
</ul>

<hr>
<address>version: <%=self.Request.getSnakeletsVersion()%></address>
</body>
</html>

