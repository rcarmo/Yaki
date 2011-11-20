<%@contenttype=text/plain%>
<%@outputencoding="iso-8859-15"%>
<%@inputencoding="iso-8859-15"%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html>
<head><title>Include test2</title></head>
<body>
<p>
<strong>First lets $include 'included.y':</strong>
<div style="border: solid black 2px;">
<!-- include included.y -->
<%$include="included.y"%>
<!-- END include included.y -->
</div>
<strong>New lets $call 'included.y':</strong>
<div style="border: solid black 2px;">
<!-- call included.y -->
<%$call="included.y?arg=123"%>
<!-- END call included.y -->
</div>
<strong>New lets $call 'included.sn':</strong>
<div style="border: solid black 2px;">
<!-- call included.sn -->
<%$call="included.sn?arg=123"%>
<!-- END call included.sn -->
</div>
<strong>Now lets $include 'incl.html':</strong>
<div style="border: solid black 2px;">
<!-- include incl.html -->
<%$include="incl.html"%>
<!-- END include incl.html -->
</div>
<strong>New lets $call 'snakelets.sf.net':</strong>
<div style="border: solid black 2px;">
<!-- call snakelets page -->
<%$call="http://snakelets.sourceforge.net"%>
<!-- END call snakelets page -->
</div>
<p>
<hr>
<address>That's it. If you don't see this line, something's rotten!!!</address>
</body>
</html>
