#
#   Access.log scanner
#   Based on a contribution by Vincent Delft
#
import re,urlparse,os.path,time,glob
import BaseHTTPServer
monthnames = BaseHTTPServer.BaseHTTPRequestHandler.monthname

class AccessLog:
    url_maxlen=200
    line_maxlen=300
    def __init__(self):
        self.data=[]
    def parse(self,filename):
        self.filename=filename
        files=glob.glob('%s.*' % filename)
        files.insert(0,filename)
        for file in files:
            content=open(file,'r').readlines()
            reg=re.compile(r'([\d\.]+) - - \[(\S+) (\S+)\] "(\S+) (\S+) (\S+)" (\d+) (-|\d+) "(\S+)" "(.+)"')
            for line in content:
                res=reg.search(line)
                if res and len(res.groups())==10:
                    ip,date,hour,cmd,url,protocol,code,size,referer,browser=res.groups()
                    self.data.append(res.groups())
 
    def analyzer(self):
        self.res={}
        self.bytessent={}
        for item in self.data:
            ip,date,hour,cmd,url,protocol,code,size,referer,browser=item
            self.bytessent.setdefault(date,0)
            if size!='-':
                self.bytessent[date]+=int(size)
            daydata=self.res.setdefault(date,{})
            detdata=daydata.setdefault('ip',{})
            if not detdata.has_key(ip): detdata[ip]=0
            detdata[ip]+=1
            detdata=daydata.setdefault('cmd',{})
            if not detdata.has_key(cmd): detdata[cmd]=0
            detdata[cmd]+=1
            detdata=daydata.setdefault('protocol',{})
            if not detdata.has_key(protocol): detdata[protocol]=0
            detdata[protocol]+=1
            detdata=daydata.setdefault('url',{})
            trunc_url=url[:self.url_maxlen]
            if not detdata.has_key(trunc_url): detdata[trunc_url]=0
            detdata[trunc_url]+=1
            page=os.path.basename(urlparse.urlparse(url)[2])
            ext=page.split('.')
            if len(ext)==2:
                detdata=daydata.setdefault('extension',{})
                if not detdata.has_key(ext[1]): detdata[ext[1]]=0
                detdata[ext[1]]+=1
            detdata=daydata.setdefault('code',{})
            if not detdata.has_key(code): detdata[code]=0
            detdata[code]+=1
            detdata=daydata.setdefault('referer',{})
            if not detdata.has_key(referer): detdata[referer]=0
            detdata[referer]+=1
            detdata=daydata.setdefault('browser',{})
            if not detdata.has_key(browser): detdata[browser]=0
            detdata[browser]+=1

    def getDateOrdered(self):
        datel = [ d.split('/') for d in self.res.keys() ] 
        datel = [ (int(y),monthnames.index(m),int(d)) for d,m,y in datel ]
        datel.sort()
        datel.reverse()
        datel=[ "%02d/%s/%04d" % (d,monthnames[m],y) for y,m,d in datel ]
        return datel
        
    def XgetDateOrdered(self):
        datel=self.res.keys()
        try:
            #strptime does not exist on all platform ...
            sort_cmd=lambda d1,d2: -cmp(time.strptime(d1,"%d/%b/%Y"),time.strptime(d2,"%d/%b/%Y"))
            datel.sort(sort_cmd)
        except: 
            pass
        return datel

    def getParameters(self):
        dates=self.res.keys()
        params=self.res[dates[0]].keys()
        params.sort()
        return params
        
    def getOrderedValues(self,date,data):
        values=[ (count, key) for key,count in self.res[date][data].items() ]
        values.sort()
        values.reverse()
        return values
               
    def XgetOrderedValues(self,date,data):
        vals=self.res[date][data].keys()
        vals.sort()
        return vals

    def getStats(self,date,daydata):
        items=len(self.res[date][daydata])
        total=0
        values= self.res[date][daydata].values()
        for val in values:
            total+=val
        maxval=max(values)
        return (items,total,maxval)

    def getRecords(self,date,key,data):
        to_replace=(('\\','\\\\'),('(','\\('),(')','\\)'),('[','\\['),(']','\\]'),('{','\\{'),('}','\\}'),('$','\\$'),('^','\\^'),('.','\\.'),('?','\\?'),('*','\\*'),('+','\\+'),('?','\\?'),('|','\\|'))
        for from_repl,to_repl in to_replace:
            data=data.replace(from_repl,to_repl)
        if key=='ip':
            reg=re.compile('%s - - \[%s (\S+)\] "(\S+) (\S+) (\S+)" (\d+) (-|\d+) "(\S+)" "(.+)"' % (data,date))
        if key=='cmd':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "%s (\S+) (\S+)" (\d+) (-|\d+) "(\S+)" "(.+)"' % (date,data))
        if key=='url':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "(\S+) %s (\S+)" (\d+) (-|\d+) "(\S+)" "(.+)"' % (date,data))
        if key=='protocol':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "(\S+) (\S+) %s" (\d+) (-|\d+) "(\S+)" "(.+)"' % (date,data))
        if key=='code':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "(\S+) (\S+) (\S+)" %s (-|\d+) "(\S+)" "(.+)"' % (date,data))
        if key=='extension':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "(\S+) (\S+).%s (\S+)" (\d+) (-|\d+) "(\S+)" "(.+)"' % (date,data))
        if key=='browser':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "(\S+) (\S+) (\S+)" (\d+) (-|\d+) "(\S+)" "%s"' % (date,data))
        if key=='referer':
            reg=re.compile('([\d\.]+) - - \[%s (\S+)\] "(\S+) (\S+) (\S+)" (\d+) (-|\d+) "%s" "(.+)"' % (date,data))
        files=glob.glob('%s.*' % self.filename)
        files.insert(0,self.filename)
        found=[]
        for file in files:
            content=open(file,'r').readlines()
            for line in content:
                if reg.search(line):
                    found.append(line[:self.line_maxlen])
        return found
    
        
            
                
