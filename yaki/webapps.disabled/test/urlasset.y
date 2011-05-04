<%@session=no%>
<%
def url2(path, arg="", params=[]):
    s=url(path,arg,params)
    return '<a href="%s">%s</a>' % (s,s)
    
def asset2(path):
    s=asset(path)
    return '<a href="%s">%s</a>' % (s, s)
%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><title>url() and asset() examples</title></head>
<body>
<h1>url() and asset() example</h1>
<p>This page shows the use of the <code>url</code> and <code>asset</code> convenience Ypage functions.
<br>(shortcuts for the <code>mkUrl</code> and <code>mkAssetUrl</code> Webapp methods)
<table border="1">
<tr><th>ypage source</th><th>resulting string</th></tr>
<tr><td colspan="2"><em>First some normal urls</em></td></tr>
<tr><td>url(&quot;&quot;)</td><td><%=url2("")%></td></tr>
<tr><td>url(&quot;/&quot;)</td><td><%=url2("/")%>  (note that the slash should not be used)</td></tr>
<tr><td>url(&quot;foo.html&quot;)</td><td><%=url2("foo.html")%></td></tr>
<tr><td>url(&quot;sub/foo.html&quot;)</td><td><%=url2("sub/foo.html")%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,&quot;arg&quot;)</td><td><%=url2("snoop.sn","arg")%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,params={&quot;q1&quot;:&quot;test&quot;, &quot;q2&quot;:&quot;42&quot;})</td><td><%=url2("snoop.sn",params={"q1":"test", "q2":"42"})%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,&quot;arg&quot;, [(&quot;q&quot;,&quot;test&quot;),(&quot;q&quot;,&quot;42&quot;)])</td><td><%=url2("snoop.sn","arg",[("q","test"), ("q","42")])%></td></tr>
<tr><td>asset(&quot;sub/foo.jpg&quot;)</td><td><%=asset2("sub/foo.jpg")%></td></tr>
<tr><td colspan="2"><em>Now some tricky urls that require escaping (click the hyperlinks to verify the result)</em></td></tr>
<tr><td>url(&quot;snoop.sn/foo with &quot; quote and spaces.html&quot;)</td><td><%=url2("snoop.sn/foo with \" quote and spaces.html")%></td></tr>
<tr><td>url(&quot;snoop.sn/foo++==.html&quot;)</td><td><%=url2("snoop.sn/foo++==.html")%></td></tr>
<tr><td>url(&quot;snoop.sn/foo?q1=42&amp;q2=43&quot;)</td><td><%=url2("snoop.sn/foo?q1=42&q2=43")%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,&quot;arg with &quot; quote and spaces and +=&quot;)</td><td><%=url2("snoop.sn","arg with \" quote and spaces and +=")%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,&quot;arg with&amp;thing=equals and/slash&quot;)</td><td><%=url2("snoop.sn","arg with&thing=equals and/slash")%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,params={'quote"name':'quote"value'})</td><td><%=url2("snoop.sn",params={'quote"name':'quote"value'})%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,params={&quot;q1&quot;:&quot;test & +=&quot;,&quot;q2 & q3&quot;:&quot;42&amp;also=43&quot;})</td><td><%=url2("snoop.sn",params={"q":"test & +=/", "q2 & q3":"42&also=43"})%></td></tr>
<tr><td>url(&quot;snoop.sn&quot;,&quot;strange / arg&quot;,{&quot;q1&quot;:&quot;test & +=&quot;,&quot;q2 & q3&quot;:&quot;42 and/or 43&quot;})</td><td><%=url2("snoop.sn","strange / arg",{"q1":"test & +=/", "q2 & q3":"42 and/or 43"})%></td></tr>
<tr><td>asset('sub/foo with &quot; quote and spaces and?ab=++blah.jpg')</td><td><%=asset2('sub/foo with " quote and spaces and?ab=++blah.jpg')%></td></tr>
<tr><td colspan="2"><em>With and without escaping</em></td></tr>
<tr><td>url(&quot;snoop.sn/with &quot; quote and &lt;&gt;.html&quot;)</td><td><%=self.escape(url("snoop.sn/with \" quote and <>.html"))%> <em>(with escaping)</em></td></tr>
<tr><td>url(&quot;snoop.sn/with &quot; quote and &lt;&gt;.html&quot;, htmlescape=False)</td><td><%=self.escape(url("snoop.sn/with \" quote and <>.html", htmlescape=False))%> <em>(without escaping; invalid html)</em></td></tr>
<tr><td>asset('sub/with &quot; quote and &lt;&gt; and?ab=++blah.jpg')</td><td><%=self.escape(asset('sub/with " quote and <> and?ab=++blah.jpg'))%> <em>(with escaping)</em></td></tr>
<tr><td>asset('sub/with &quot; quote and &lt;&gt; and?ab=++blah.jpg',htmlescape=False)</td><td><%=self.escape(asset('sub/with " quote and <> and?ab=++blah.jpg',htmlescape=False))%> <em>(without escaping; invalid html)</em></td></tr>
</table>
</body>
</html>
