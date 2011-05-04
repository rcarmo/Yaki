class YBaseClass:
    def create(self,out,_request,_response):
        print >>out,'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
        print >>out, "<html><head><title>Page inheritance demo</title></head>"
        print >>out, "<body><h2>This is the header. It is created from the base class YBaseClass</h2>"
        print >>out, "<p>Below, the 'real' page output is visible:<hr>"
        print >>out,"<div style='margin: 10pt; background-color: #d0d0d0;'>"
        self.generateHTML(out,_request,_response)
        print >>out,"</div>"
        print >>out, "<hr><p>And this is the footer, again created from the base class."
        print >>out, "Using this mechanism, it is quite easy to create a template-like setup for your website."
        print >>out, "<p>If you're not using the 'real' template mechanism of Ypages, ofcourse :-)"
        print >>out, "(with the &lt;%@pagetemplate=&quot;...&quot;%&gt; declaration)"
        print >>out, "</body></html>"
