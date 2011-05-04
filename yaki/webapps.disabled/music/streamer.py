import os,sys
import mp3.ID3
from snakeserver.snakelet import Snakelet


class Streamer(Snakelet):
	def init(self):
		self.getAppContext().active_streams={}
		self.openConnections={}

	def getDescription(self):
		return "Serves streaming MP3"

	def requiresSession(self):
		return self.SESSION_NOT_NEEDED  
		
	def serve(self, request, response):
		form=request.getForm()
		if form.has_key('disconnect'):
			ip=form['disconnect']
			try:
				for resp in self.openConnections[ip]:
					resp.kill()
			except KeyError:
				pass
			response.getOutput().write("<html><body>All connections from "+ip+" have been cancelled.")
			response.getOutput().write("<p><a href=\".\">Go back.</a></body></html>")
			return

		frm=0
		to=sys.maxint
		rng = request.getRange()
		if rng:
			(frm,to)=rng
			# must return code 206 Partial Content...
			response.setResponse(206,"Partial Content")

		if form.has_key('id'):
			try:
				fid=int(form['id'])
				# get the scanner from the module context
				scanner=self.getAppContext().scanner
				result = scanner.getByFileID(fid)
				if result:
					import stat,socket
					filename = os.path.join(result[0],result[1])
					length = os.stat(filename)[stat.ST_SIZE]
					length = 1+ min(length-1, (to-frm))
					file=open(filename,'rb')
					file.seek(frm)
					if result[2]:
						songName=result[2].artist+' - '+result[2].title
						genre=mp3.ID3.getGenreString(result[2].genre)
					else:
						# There is no ID3 tag; use the filename as songname. Strip path info.
						songName=os.path.basename(filename)
						genre="unknown"
					icyname=songName+'  {stream}'
					response.setContentType("audio/mpeg")
					response.setContentLength(length)
					response.setHeader("icy-notice1","This stream requires a streaming-MP3 player")
					response.setHeader("icy-notice2","Python Streaming MP3 Server")
					response.setHeader("icy-name",icyname)
					response.setHeader("icy-genre",genre)
					response.setHeader("icy-pub","0")
					# response.setHeader("icy-url",self.getFullURL())
					# response.setHeader("icy-br","128")
					# response.setHeader("icy-metaint","0")
					
					streams = self.getAppContext().active_streams
					streams.setdefault(request.getRemoteHost(), []).append(filename)
					self.openConnections.setdefault(request.getRemoteHost(), []).append(response)
					try:
						try:
							# loop as long as errorSent is not set (will be set if response is killed/aborted)
							while not response.wasErrorSent():		
								buf = file.read(64*1024)
								if not buf:
									break
								response.getOutput().write(buf)
						except socket.error:
							# silently abort the transmission
							pass
					finally:
						streams = self.getAppContext().active_streams[request.getRemoteHost()]
						streams.remove(filename)
						openConns=self.openConnections[request.getRemoteHost()]
						openConns.remove(response)
						if not openConns:
							# all streams to this client have stopped, remove the client
							del self.openConnections[request.getRemoteHost()]
						if not streams:
							# all streams to this client have stopped, remove the client
							del self.getAppContext().active_streams[request.getRemoteHost()]
						return
				else:
					response.sendError(404, "Record not found.")
			except ValueError:
				response.sendError(501, "Invalid command args")
		else:
			response.sendError(501, "Invalid command args")

