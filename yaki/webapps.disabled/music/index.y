<%@session=no%>
<%@import=import streamer,time%>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><title>Music browser</title>
<style type="text/css">
<!--
body,td,th {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 10pt;
	color: #000000;
}
body {
	background-color: #EEFFFF;
}
h1 { font-size: 14pt; }
h2 { font-size: 12pt; }
table {
    background-color: #ccffcc;
}
th {
    background-color: navy;
    color: yellow;
}
-->
</style></head>
<body><h2>Python MP3 Stream Server</h2>
<%s=self.ApplicationCtx.scanner
byGenre= s.filterByGenre()
byAlbum= s.filterByAlbum()
byYear= s.filterByYear()
byTitle= s.filterByTitle()
byArtist= s.filterByArtist()
byDir = s.getAllMP3dirs()


# initialize music streaming URL parameters
if not self.ApplicationCtx.streamURLbase:
	self.ApplicationCtx.streamURLbase = self.Request.getBaseURL()
%>

<%if s.getTotalMP3FileCount()==0:%>
<h3><em>No MP3s in the database, or no database has been loaded.</em>
<br><em>(you have to create a mp3 database file using the <code>makedatabase.py</code> script!)</em></h3>
<%end%>

<table border="1" summary="database information">
  <tr> 
    <th colspan="3">Database Statistics</th>
  </tr>
  <tr><td>Last scanned </td><td><%=time.ctime(s.lastScanned)%></td></tr>
  <tr> 
    <td>Directories scanned </td>
    <td><%self.write('<br>'.join(s.scannedDirs))%></td>
  </tr>
  <tr> 
    <td>Total number of MP3s</td>
    <td><%self.write(s.getTotalMP3FileCount())%></td>
  </tr>
  <tr> 
    <td>Genres</td>
    <td><%=len(byGenre)%></td>
  </tr>
  <tr> 
    <td>Titles</td>
    <td><%=len(byTitle)%></td>
  </tr>
  <tr> 
    <td>Artists</td>
    <td><%=len(byArtist)%></td>
  </tr>
  <tr> 
    <td>Albums</td>
    <td><%=len(byAlbum)%></td>
  </tr>
  <tr> 
    <td>Years</td>
    <td><%=len(byYear)%></td>
  </tr>
  <tr>
    <td>Directories</td>
    <td><%=len(byDir)%></td>
  </tr>
</table>
<p>
<form name="form1" method="post" action="music.sn">
<p>
  <strong>Browse the database by category: 
  <select name="cat">
    <option selected>artist</option>
    <option>album</option>
    <option>title</option>
    <option>file</option>
    <option>dir</option>
    <option>genre</option>
    <option>year</option>
  </select>
  <input type="submit" name="q" value="browse"></strong>
  <br>
  Reload the database: <input type="submit" name="q" value="reload">
</form>
<form method="post" action="music.sn">
<p>
MP3 player stream URL base (usually the current hostname:port): <code><%=self.ApplicationCtx.streamURLbase%></code>
<br>You may have to change this URL if this server is running behind a proxy (see also webapp configItems for default override).
<br><input type="text" name="urlbase" size="20" value="<%=self.ApplicationCtx.streamURLbase%>"> <input type="submit" name="q" value="change url">
</form>
<table border="1" cellspacing="1" cellpadding="1" summary="open connections">
<%streams=self.ApplicationCtx.active_streams%>
<tr><th colspan="3">Currently listening: <%=len(streams)%> clients</th></tr>
<%for (host,files) in streams.items():
	self.write('<tr><td><a href="streamer.sn?disconnect='+host+'">disconnect</a></td><td><strong>'+host+'</strong></td><td>'+'<br>'.join(files)+'</td></tr>\n')
%>
</table>
<p>
<p>
<hr>
<address><%=self.Request.getServerSoftware()%></address>
</body></html>
