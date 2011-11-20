<%@outputencoding="UTF-8"%>
<%@inputencoding="UTF-8"%>
<html>

<head> 
    <!-- Since we're on a secondary wiki that is not on a separate virtual host, the BASE tag makes it a lot easier to manage URLs -->
    <base href="/secondary/" />
	<title>Yaki - <%=self.Request.getParameter('title','Template')%></title>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="generator" content="Yaki" />
	<meta name="template" content="Minimal" />
 	<meta name="description" content="" />	<link rel="alternate" type="application/rss+xml" title="RSS 2.0" href="/feed" />
	<link rel="alternate" type="text/xml" title="RSS .92" href="/feed/rss" />
	<link rel="alternate" type="application/atom+xml" title="Atom 0.3" href="/feed/atom" />

<style>
 body { font-family: "Helvetica Neue", Helvetica, Arial, "Liberation Sans", sans-serif; text-rendering:optimizeLegibility; }
	  header {text-align: center; font-size: 2em;}
	  pre, code { font-family: Menlo, Monaco, Consolas, "Lucida Console", "Courier New", Courier, monospaced; font-size: 0.85em; word-wrap: break-word;}
a { color: #89a; text-decoration: none; }
a:hover { color: blue; }
table tr td { font-size: 0.8em; padding: 2px; }
table tr:hover { background-color: #abc; color: #448; -webkit-border-radius: 8px; }
</style>
<body>
<div id="page">
	<div id="header">

    <h1 id="site-title"><a href="p/start"><%=self.Request.getParameter('site_name', 'Yaki Wiki Engine')%></a></h1>
    <div id="site-description"><%=self.Request.getParameter('site_description','Powered by Python. Dipped in BeautifulSoup. Flavored with Snakelets.')%></div>

<div class="headermenu">
	<ul>
	
<%
links = [
  ['p/start','Home Page', 'Home'],
  ['p/meta/RecentChanges','Recent Changes', 'Recent Changes'],
]

for i in links:
  if i[0] == self.Request.getParameter('path', 'meta/EmptyPage'):
    css = "current_page_item"
  else:
    css = "page_item"
  self.write( '<li class="%s"><a href="%s" title="%s">%s</a></li>' % (css, i[0], i[1], i[2]))  
%>
	</ul>
</div>
	</div>
<hr />

<div class="wrapper">
  <div class="primary">
    <div class="content hfeed">
          <%=self.Request.getParameter('postbody','')%>
    </div><!-- #primarycontent .hfeed -->
  </div> <!-- #primary -->
  <hr />
  <div class="secondary">
<form method="get" action="p/meta/Search" method="get">
	<input type="text" name="q" tabindex="1" autocomplete="off" value="Search" />
	<input type="submit" id="searchsubmit" value="go" />
</form>
  </div>
</div>
<div class="clear"></div>
</div> <!-- .content -->
<div class="clear"></div>
</div> <!-- Close Page -->
<hr/>
<p id="footer"><small>
Powered by Yaki
</small></p>
</body>
</html> 
