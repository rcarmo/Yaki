<%@session=yes%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Cookies ok</title>
<script type="text/javascript">
<!--
  function getCookie(name) { // use: getCookie("name");
    var re = new RegExp(name + "=([^;]+)");
    var value = re.exec(document.cookie);
    return (value != null) ? unescape(value[1]) : null;
  }
  
if(getCookie("SNSESSID")==null && getCookie("SNSESSIDSHR")==null)
{
	if(document.location.href.indexOf("?nocookies")<0)
		document.location.href="cookiejs.y?nocookies";
}

-->
</script>
</head>
<body>
<%
if self.Request.getArg()=="nocookies":
%>
<p>Your browser refused the session cookie for this website.</p>
<p>Please enable cookies, and <a href="<%=self.getURL()%>">try again</a>.</p>
<%else:%>
<p>Your browser accepted the session cookie.  Everything is fine :-)</p>
<p>Try disabling cookies now, and reload this page...</p>
<%end%>
</body>
</html>
