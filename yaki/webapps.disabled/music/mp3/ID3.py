import string

class NoTagFoundError(Exception): pass

genres = ( "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk",
	"Grunge", "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other",
	"Pop", "R&B", "Rap", "Reggae", "Rock", "Techno", "Industrial",
	"Alternative", "Ska", "Death Metal", "Pranks", "Soundtrack",
	"Euro-Techno", "Ambient", "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion",
	"Trance", "Classical", "Instrumental", "Acid", "House", "Game",
	"Sound Clip", "Gospel", "Noise", "Alternative Rock", "Bass", "Soul",
	"Punk", "Space", "Meditative", "Instrumental Pop", "Instrumental Rock",
	"Ethnic", "Gothic", "Darkwave", "Techno-Industrial", "Electronic",
	"Pop-Folk", "Eurodance", "Dream", "Southern Rock", "Comedy",
	"Cult", "Gangsta", "Top 40", "Christian Rap", "Pop/Funk", "Jungle",
	"Native American", "Cabaret", "New Wave", "Psychadelic", "Rave",
	"Showtunes", "Trailer", "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz",
	"Polka", "Retro", "Musical", "Rock & Roll", "Hard Rock", "Folk",
	"Folk/Rock", "National Folk", "Swing", "Fusion", "Bebob", "Latin",
	"Revival", "Celtic", "Bluegrass", "Avantgarde", "Gothic Rock",
	"Progresssive Rock", "Psychadelic Rock", "Symphonic Rock", "Slow Rock",
	"Big Band", "Chorus", "Easy Listening", "Acoustic", "Humour",
	"Speech", "Chanson", "Opera", "Chamber Music", "Sonata", "Symphony",
	"Booty Bass", "Primus", "Porn Groove", "Satire", "Slow Jam",
	"Club", "Tango", "Samba", "Folklore", "Ballad", "Power Ballad",
	"Rhythmic Soul", "Freestyle", "Duet", "Punk Rock", "Drum Solo",
	"A Capella", "Euro-House", "Dance Hall", "Goa", "Drum & Bass",
	"Club-House", "Hardcore", "Terror", "Indie", "BritPop", "Negerpunk",
	"Polsk Punk", "Beat", "Christian Gangsta Rap", "Heavy Metal",
	"Black Metal", "Crossover", "Contemporary Christian", "Christian Rock",
	"Merengue", "Salsa", "Thrash Metal", "Anime", "Jpop", "Synthpop" )
	
def getGenreString(genreidx):
	if genreidx<0 or genreidx>=len(genres):
		return '??'
	else:
		return genres[genreidx]		

class ID3:
	def __init__(self, file=None):
		if file:
			self.readFromFile(file)
		else:
			self.title=''
			self.artist=''
			self.album=''
			self.year=''
			self.comment=''
			self.genre=255
			self.track=None
			self.filename=None

	def readFromFile(self,file):
		f=open(file,'rb')
		f.seek(-128,2)
		self.initFromTag(f.read(128))
		f.close()
		self.filename=file

	def writeToFile(self,file):
		f=open(file,'rb+')
		f.seek(-128,2)
		t=f.read(128)
		if t[:3]=='TAG' and len(t)==128:
			f.seek(-128,2)		# overwrite tag
		else:
			f.seek(0,2)		# append new tag at end
		f.write(self.makeTag())
		f.close()

	def initFromTag(self,tag):
		if tag[:3]=='TAG' and len(tag)==128:
			self.title = self.trim(tag[3:33])
			self.artist = self.trim(tag[33:63])
			self.album = self.trim(tag[63:93])
			self.year = self.trim(tag[93:97])
			self.comment = tag[97:127]
			self.genre = ord(tag[127])
			if ord(self.comment[-2]) == 0 and ord(self.comment[-1]) != 0:
				self.track = ord(self.comment[-1])
				self.comment = self.comment[:-2]
			else:
				self.track = None
			self.comment=self.trim(self.comment)
		else:
			raise NoTagFoundError

	def makeTag(self):
		if self.genre<0 or self.genre>=len(genres):
			genre=chr(255)
		else:
			genre=chr(self.genre)
		tag='TAG'+self.fill(self.title,30)+self.fill(self.artist,30)+self.fill(self.album,30)+self.fill(self.year,4)
		comment=self.fill(self.comment,30)
		if self.track != None:
			comment=comment[:-2]+'\0'+chr(self.track)
		return tag+comment+genre

	def __str__(self):
		if self.track!=None:
			track=str(self.track)
		else:
			track='??'
		if self.genre<0 or self.genre>=len(genres):
			genre='??'
			genreidx=255
		else:
			genre=genres[self.genre]
			genreidx=self.genre
		if self.filename:
			filename=self.filename
		else:
			filename='<not from a file>'
		return "File   : %s\nTitle  : %-30.30s  Artist: %-30.30s\nAlbum  : %-30.30s  Track : %s  Year: %-4.4s\nComment: %-30.30s  Genre : %s (%i)" % (filename, self.title, self.artist, self.album, track, self.year, self.comment, genre, genreidx)

	def trim(self,s):
		if len(s)>0 and s[0]=='\0':
			return ""
		s=string.rstrip(s)
		while len(s)>0 and s[-1]=='\0':
			s=s[:-1]
		return s

	def fill(self,s,len):
		s=s+'\0'*len
		return s[:len]


