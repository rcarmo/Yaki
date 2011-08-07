#
#   MP3 'jukebox' 
#   created by Irmen de Jong
#   contributions by Per Ersson
#

import os,time,urllib
import mp3.mp3tool
import streamer

from snakeserver.snakelet import Snakelet


class Playlist(Snakelet):

    def init(self):
        pass

    def requiresSession(self):
        return self.SESSION_NOT_NEEDED

    def getDescription(self):
        return "creates dynamic MP3-playlists"

    def serve(self, request, response):
        form=request.getForm()
        if form.has_key('q') and form.has_key('id'):
            query=form['q']
            fid=int(form['id'])
            scanner=self.getAppContext().scanner
            if query=="play":
                resultlist = []
                resultlist.append(scanner.getByFileID(fid))
                self.playset(request,response,resultlist)
            elif query=="playdir":
                resultlist = scanner.getByDirID(fid)
                resultlist.sort()
                self.playset(request,response, resultlist)
            elif query=="playgroup":
                cat=form['cat'].lower()
                resultset = []
                if cat=="genre":
                    resultset = self.getResultset(scanner.filterByGenre(),fid)
                elif cat=="artist":
                    resultset = self.getResultset(scanner.filterByArtist(),fid)
                elif cat=="album":
                    resultset = self.getResultset(scanner.filterByAlbum(),fid)
                elif cat=="title":
                    resultset = self.getResultset(scanner.filterByTitle(),fid)
                elif cat=="year":
                    resultset = self.getResultset(scanner.filterByYear(),fid)
                elif cat=="file":
                    # Ha, we know how to handle this easily, kick it
                    # to the 'play' command for this file ID.
                    URL=self.getURL()+'?q=play&id='+form['id']
                    response.HTTPredirect(URL)
                elif cat=="dir":
                    # Ha, we know how to handle this easily, kick it
                    # to the 'play' command for this file ID.
                    URL=self.getURL()+'?q=playdir&id='+form['id']
                    response.HTTPredirect(URL)
                self.playset(request,response, resultset)
            else:
                response.sendError(503, "Invalid command specified")
        else:
            response.sendError(502, "Invalid command specified")

    def getResultset(self, result, fid):
        for rr in result.keys():
            if fid == id(rr):
                return result[rr]
        return []
        
    def playset(self,request,response, resultset):
        try:
            streamerURL = urllib.basejoin(self.getWebApp().getURLprefix(), "streamer.sn")
            baseURL=self.getAppContext().streamURLbase or request.getBaseURL()
            reply = "#EXTM3U\n"
            for result in resultset:
                reply=reply + "#EXTINF:-1," + result[1] + '\n' + \
                       urllib.basejoin(baseURL,streamerURL+'?id='+`id(result[1])`)+'\n'
            # response.setContentType("audio/x-mpegurl")
            response.setContentType("audio/mpegurl")
            response.setContentLength(len(reply))
            response.getOutput().write(reply)
        except ValueError:
            response.sendError(501, "Invalid command args")


class Music(Snakelet):

    def init(self):
        self.getAppContext().database = os.path.join(self.getAppContext().AbsPath,"database.bin")
        self.loadDatabase()
        # initialize music streaming URL parameters
        self.getAppContext().streamURLbase = self.getWebApp().getConfigItems().get("stream_url_base")

    def requiresSession(self):
        return self.SESSION_NOT_NEEDED

    def getDescription(self):
        return "Browse music database"

    def loadDatabase(self):
        ctx=self.getAppContext()
        print " loading MP3 database",ctx.database
        scanner = mp3.mp3tool.MP3Scanner()
        try:
            scanner.readFromDisk(ctx.database)
            print " last scanned ",time.ctime(scanner.lastScanned)
            print " scanned dirs:",
            for d in scanner.scannedDirs:
                print d,
            print
        except IOError:
            print
            print
            print "**** Music webapp cannot load database"
            print "**** You have to create a mp3 database file!"
            print "**** (use the makedatabase.py script for this)"
            print 
            print
            
        # store the scanner in the module context, so other servlets can access it too
        self.getAppContext().scanner = scanner
        
    def serve(self, request, response):
        form=request.getForm()
        if form.has_key('q'):
            query=form['q']
            if query=="browse":
                self.browse(request, response)
            elif query=="reload":
                self.loadDatabase()
                # musicYpage=urllib.basejoin(self.getAppContext().UrlPrefix,"index.y")
                response.HTTPredirect(".")
            elif query=="change url":
                self.getAppContext().streamURLbase = form['urlbase']
                response.HTTPredirect(".")
            else:
                response.sendError(501, "Invalid command specified")
        else:
            response.sendError(404,"not found")

    def browse(self, request,response):
        form=request.getForm()
        if form.has_key('cat'):
            cat = form["cat"]
            s = self.getAppContext().scanner 
            out=response.getOutput()
            print >>out,'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
            print >>out, '<html><head><title>Mp3 server</title></head><body bgcolor="#CCFFFF"><a href="index.y"><img src="img/back.gif" border="0" align="middle"> Back to main</a> '
            if cat=="genre":
                self.printHTMLlist("Genre",out, s.filterByGenre(), request)
            elif cat=="artist":
                self.printHTMLlist("Artist",out, s.filterByArtist(), request)
            elif cat=="album":
                self.printHTMLlist("Album",out, s.filterByAlbum(), request)
            elif cat=="title":
                self.printHTMLlist("Song Title",out, s.filterByTitle(), request)
            elif cat=="file":
                self.printHTMLlist("File",out, s.filterByFile(), request)
            elif cat=="year":
                self.printHTMLlist("Year",out, s.filterByYear(), request)
            elif cat=="dir":
                self.printHTMLdirlist("Path",out,s.getAllMP3dirs())
            else:
                print >>out, "invalid category"
            print >>out, "</body></html>"
        else:
            response.sendError(501, "Invalid command args")


    # Print a listing by a selected category

    def printHTMLlist(self, caption, out, list, request):
        out.write('<p><strong>Sorted by '+caption+'</strong>')
        out.write('<table border=1><tr bgcolor="#005000"><th><font color="white">%s</font><th><font color="white">Path and Files</font>\n' % caption)
        keys=list.keys()
        keys.sort()
        playlistURL = 'stream.m3u'
        counter=1
        for name in keys:
            items=list[name]
            items.sort()
            playGroupURL=playlistURL+'?q=playgroup&id='+`id(name)`+'&cat='+request.getForm()['cat']
            output = ('<tr><td valign=top rowspan=@@NUMITEMS@@ bgcolor="#500000"><font color="#ffe0a0">&nbsp;<a href="%s"><img src="img/play.gif" border=0></a>&nbsp;%s</font>\n' % (playGroupURL, str(name)) )
            numItems=0
            prevDir=None
            for (dir,file,id3) in items:
                playURL=playlistURL+'?q=play&id='+`id(file)`
                playDirURL=playlistURL+'?q=playdir&id='+`id(dir)`
                if dir!=prevDir:
                    output+=('<td bgcolor="#000050">&nbsp;&nbsp;<a href="%s"><img src="img/play.gif" border=0></a>&nbsp;&nbsp;<font color="#a0e0ff">%s</font>\n<tr>' % (playDirURL,dir))
                    prevDir=dir
                    numItems+=1
                output+=('<td>&nbsp;&nbsp;&nbsp;<a href="%s"><img src="img/play.gif" border="0"></a>&nbsp;&nbsp;&nbsp;%s\n<tr>' % ( playURL,file))
                numItems+=1
                counter+=1
            # strip last <tr> and set the now known rowspan
            out.write(output[:-4].replace('@@NUMITEMS@@',str(numItems)))
            if counter>=self.getWebApp().getConfigItem("max_results"):
                out.write('</table>\n<p><strong>There are more than %d results. The rest is not shown.</strong>' % self.getWebApp().getConfigItem("max_results"))
                return
        out.write("</table>\n")


    # Prints a dir--file overview (directory listing)

    def printHTMLdirlist(self, caption, out, list):
        out.write('<table border=1><tr bgcolor="#005000"><th><font color="white">%s</font><th><font color="white">Files</font>\n' % caption)
        keys=list.keys()
        keys.sort()
        playlistURL = 'stream.m3u'
        for d in keys:
            files=list[d]
            files.sort()
            firstRow=True
            playDirURL=playlistURL+'?q=playdir&id='+`id(d)`
            print >>out, '<tr><td valign=top rowspan=%d  bgcolor="#500000"><a href="%s"><img src="img/play.gif" border=0></a>&nbsp;&nbsp;<font color="#ffe0a0">%s</font>' % (len(files), playDirURL, d)
            for (file,id3) in files:
                playURL=playlistURL+'?q=play&id='+`id(file)`
                if not firstRow:
                    out.write('<tr>')
                out.write('<td>&nbsp;&nbsp;&nbsp;<a href="%s"><img src="img/play.gif" border="0"></a>&nbsp;&nbsp;&nbsp;%s\n' % ( playURL,file))
                firstRow=False
        out.write('</table>')   

