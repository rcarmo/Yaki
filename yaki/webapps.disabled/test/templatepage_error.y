<%@pagetemplate="Template.y"%>
<%@pagetemplatearg=title=Template page with error%>
<%@pagetemplatearg=page=A templated page with an error inside%>
<hr><p>
Going to devide one by zero..
You should see a custom error page (red) instead of the default errorpage.
<%a=1/0%>
That's it
</hr>

