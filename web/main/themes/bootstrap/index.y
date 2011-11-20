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
<% self.Assetprefix = 'themes/bootstrap/' %>
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
      <script src="/themes/bootstrap/js/html5.js"></script>
    <![endif]-->

    <!-- Le styles -->
    <link href="/themes/bootstrap/css/bootstrap.css" rel="stylesheet">
    <link href="/themes/bootstrap/css/syntax.css" rel="stylesheet">
    <style type="text/css">
      /* Override some defaults */
      html, body {
        background-color: #eee;
      }
      body {
        padding-top: 40px; /* 40px to make the container go all the way to the bottom of the topbar */
      }
      .container > footer p {
        text-align: center; /* center align it with the container */
      }
      .container {
        width: 820px; /* downsize our container to make the content feel a bit tighter and more cohesive. NOTE: this removes two full columns from the grid, meaning you only go to 14 columns and not 16. */
      }

      /* The white background content wrapper */
      .content {
        background-color: #fff;
        padding: 20px;
        margin: 0 -20px; /* negative indent the amount of the padding to maintain the grid system */
        -webkit-border-radius: 0 0 6px 6px;
           -moz-border-radius: 0 0 6px 6px;
                border-radius: 0 0 6px 6px;
        -webkit-box-shadow: 0 1px 2px rgba(0,0,0,.15);
           -moz-box-shadow: 0 1px 2px rgba(0,0,0,.15);
                box-shadow: 0 1px 2px rgba(0,0,0,.15);
      }

      /* Page header tweaks */
      .page-header {
        background-color: #f5f5f5;
        padding: 20px 20px 10px;
        margin: -20px -20px 20px;
      }

      /* Styles you shouldn't keep as they are for displaying this base example only */
      .content .span10,
      .content .span4 {
        min-height: 500px;
      }
      /* Give a quick and non-cross-browser friendly divider */
      .content .span4 {
        margin-left: 0;
        padding-left: 19px;
        border-left: 1px solid #eee;
      }

      .topbar .btn {
        border: 0;
      }

    </style>

    <!-- Le fav and touch icons -->
    <link rel="shortcut icon" href="/themes/bootstrap/img/favicon.ico">
    <link rel="apple-touch-icon" href="/themes/bootstrap/img/bootstrap-apple-57x57.png">
    <link rel="apple-touch-icon" sizes="72x72" href="/themes/bootstrap/img/bootstrap-apple-72x72.png">
    <link rel="apple-touch-icon" sizes="114x114" href="/themes/bootstrap/img/bootstrap-apple-114x114.png">
  </head>

  <body>

    <div class="topbar">
      <div class="fill">
        <div class="container">
          <a class="brand" href="/p/start"><%=ac.siteinfo['sitename']%></a>
          <ul class="nav">
            <li class="active"><a href="/p/start">Home</a></li>
            <li><a href="/p/site/about">About</a></li>
          </ul>
          <form  action="/p/meta/Search" method="get" accept-charset="utf-8" class="pull-right">
            <input class="input-small" name="q" type="text" placeholder="Search">
            <button class="btn" type="submit">Go</button>
          </form>
        </div>
      </div>
    </div>

    <div class="container">

      <div class="content">
        <div class="page-header">
          <h1><%=self.Request.getParameter('title','Untitled Page')%>
 <small><!-- TODO: add metadata here --></small></h1>
        </div>
        <div class="row">
          <div class="span10">
            <%=self.Request.getParameter('postbody','')%>
          </div>
          <div class="span4">
            <h3>Links</h3>
            <ul>
            <li><a href="/p/meta/Archives">Archives</a></li>
            <li><a href="/p/meta/Index">Index</a></li>
            <li><a href="/p/meta/RecentUpdates">Recent Updates</a></li>
             </ul>
          </div>
          <div class="span14">
          <%=self.Request.getParameter('seealso','')%>
          </div>
        </div>
      </div>

      <footer>
        <p>Powered by <a href="https://github.com/rcarmo/Yaki">Yaki</a>. Themed by <a href="http://twitter.github.com/bootstrap/">Bootstrap</a>. Batteries included.</p>
      </footer>

    </div> <!-- /container -->

  </body>
</html>
