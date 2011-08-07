<%@outputencoding="UTF-8"%>
<%@inputencoding="UTF-8"%>
<%@allowcaching=no%>
<%
self.setHeader("Pragma",'no-cache')
self.setHeader("Cache-Control",'max-age=0')
%>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Please Wait...</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<base href="<% self.Request.getBaseURL() %>/space/">
<meta name="generator" content="Snakelets">
<meta http-equiv="REFRESH" content="10;">
<link rel="stylesheet" href="/themes/k2/style.css" type="text/css" media="screen">
<script language="javascript" type="text/javascript" src="/js/site-min.js"></script>
</head>
<body>
<div id="page">
  <div id="content">
  <script type="text/javascript">
  $(document).ready(function() {
    setTimeout( "location.reload()", 10*1000 );
  });
  </script>
  <center><h3>Server Starting</h3><p>You will be taken to the page in a few seconds.</p><p>&nbsp;</p><p><img src="/img/progressbar.gif"></p><p>&nbsp;</p><p><small>(if nothing happens empty your browser cache and hit refresh, or try going <a href="/space">directly</a> to the home page.)</small></p></center>
  </div>
</div>
</body>
</html>
