<%@pagetemplate="Template.y"%>
<%@pagetemplatearg=title=Title one%>
<%@pagetemplatearg=page=first page with plus + and ampersand &%>
<%@import=import time%>
<%@method=templateArgs(self, request):
    # return a custom, dynamic, template arg
    return { "timestamp": time.time() }
%>
<hr><p>This is the contents in the templated page #1
<hr>