<%@errorpage="errorpage.y"%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><title>Template page example</title></head>
<body>
<p>
Hello, this is a templated page. The values in the block below
are specified in the page itself using template args.
<br>
The timestamp arg is determined dynamically using a special custom page
method <code>templateArgs</code>.
<br>
The page also has a custom errorpage defined.
<p>
<div style="border: dotted blue 2px; width: 80ex;">
TITLE: <em><%=self.PageArgs.get('title','')%></em>
<br>
This will be page: <em><%=self.PageArgs.get('page','??')%></em> 
<br>timestamp: <em><%=self.PageArgs.get('timestamp','??')%></em> (dynamic; try reloading the page)
</div>
<p>
This is the template text. Actual page follows:
<!-- INSERT PAGE -->
<%$insertpagebody%>
<!-- END INSERTED PAGE -->
<p>
This is again the template text.

</body>
</html>
