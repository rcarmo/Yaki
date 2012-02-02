<%@outputencoding="UTF-8"%>
<%@inputencoding="UTF-8"%>
<%@session=dontcreate%>
<%
import time
import datetime
self.setHeader("Last-Modified",self.Request.getParameter('lastmodified',''))
self.setHeader("Etag", self.Request.getParameter('etag',''))
self.setHeader("Cache-Control", self.Request.getParameter('cachecontrol','public, max-age=86400'))
self.setHeader("Expires", self.Request.getParameter('expires',(datetime.datetime.utcnow() + datetime.timedelta(seconds=3600*24*30)).strftime('%a, %d %b %Y %H:%M:%S GMT')))
#unset these headers to force browsers to rely on Last-Modified and etag
ac = self.ApplicationCtx
%>
<% self.Assetprefix = 'theme/%s/' % self.Request.getParameter('theme', '') %>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title><%=self.Request.getParameter('title','Untitled Page')%> - <%=ac.siteinfo['sitename']%></title>
    <meta name="keywords" content="<%=self.Request.getParameter('keywords','')%>" />
    <meta name="description" content="">
    <meta name="author" content="">
    <!-- Le HTML5 shim, for IE6-8 support of HTML elements -->
    <!--[if lt IE 9]>
      <script src="/themes/<%=self.Request.getParameter('theme', '')%>/js/html5.js"></script>
    <![endif]-->
    <!-- Le styles -->
    <link href="/themes/<%=self.Request.getParameter('theme', '')%>/css/bootstrap.css" rel="stylesheet">
    <link href="/themes/<%=self.Request.getParameter('theme', '')%>/css/syntax.css" rel="stylesheet">
    <style type="text/css">
      /* Override some defaults */
      html, body {
        background-color: #eee;
      }
      .content {
        background-color: #fff;
        padding: 1em;
      }
      body {
        padding-top: 60px;
        padding-bottom: 40px;
      }
      .sidebar-nav {  padding: 9px 0;      }
    </style>

    <!-- Le fav and touch icons -->
    <link rel="shortcut icon" href="/themes/<%=self.Request.getParameter('theme', '')%>/img/favicon.ico">
    <link rel="apple-touch-icon" href="/themes/<%=self.Request.getParameter('theme', '')%>/img/apple-touch-icon-57x57.png">
    <link rel="apple-touch-icon" sizes="72x72" href="/themes/<%=self.Request.getParameter('theme', '')%>/img/apple-touch-icon-72x72.png">
    <link rel="apple-touch-icon" sizes="114x114" href="/themes/<%=self.Request.getParameter('theme', '')%>/img/apple-touch-icon-114x114.png">
  </head>

  <body>

    <div class="navbar navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container-fluid">
          <a class="brand" href="/<%=self.Request.getParameter('siteroot', '')%>/start"><%=ac.siteinfo['sitename']%></a>
          <div class="nav-collapse">
            <ul class="nav">
                <li class="active"><a href="/<%=self.Request.getParameter('siteroot', '')%>/start">Home</a></li>
                <li><a href="/<%=self.Request.getParameter('siteroot', '')%>/site/about">About</a></li>
            </ul>
            <form action="/<%=self.Request.getParameter('siteroot', '')%>/meta/Search" method="get" accept-charset="utf-8" class="pull-right navbar-search">
            <input class="search-query span2" name="q" type="text" placeholder="Search">
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="container-fluid">
      <div class="page-header">
          <h1><%=self.Request.getParameter('title','Untitled Page')%><small><!-- TODO: add metadata here --></small></h1>
      </div>
      <div class="row-fluid">
            <div class="span9">
              <div class="content">
                <%=self.Request.getParameter('postbody','')%>
      <hr>
                <%
if self.Request.getParameter('path', '') != "home":
  self.write( '%s' % self.Request.getParameter('seealso',''))
%>

              </div>
            </div>
            <div class="span3">
              <div class="well sidebar-nav">
                <ul class="nav nav-list">
                <li class="nav-header">Links</li>
                <li><a href="/<%=self.Request.getParameter('siteroot', '')%>/meta/Archives">Archives</a></li>
                <li><a href="/<%=self.Request.getParameter('siteroot', '')%>/meta/Index">Index</a></li>
                <li><a href="/<%=self.Request.getParameter('siteroot', '')%>/meta/RecentUpdates">Recent Updates</a></li>
                </ul>
              </div>
            </div>
     </div>
      <hr>
      <footer>
        <p>Powered by <a href="https://github.com/rcarmo/Yaki">Yaki</a>. Themed by <a href="http://twitter.github.com/bootstrap/">Bootstrap</a>. Batteries included.</p>
      </footer>

    </div> <!-- /container -->

  </body>
</html>
