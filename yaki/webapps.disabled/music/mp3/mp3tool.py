#! /usr/local/bin/env python


#
#	NOTES ON UNIQUE IDs
#
#	Individual Files can be uniquely identified by  id(file) -- the python ids of the filename
#		(note that the dir scan algorithm creates new filename strings for each directory,
#		 even if the file appears multiple times in different directories).
#
#	Directories can be identified by  id(dir) -- the python id of the directory
#		(because directories are stored in fully expanded absolute form)
#
#	Albums can be identified by  id(albumname) 
#
#	Artists can be identified by  id(artist)
#
#	Genres are uniquely identified by their Genre ID or string.
#	Years are uniquely identified by the year itself.
#	


from ID3 import *

import os,sys,string,time
try:
	import cPickle as pickle
except ImportError:
	import pickle


suffixes = ('.mp3','.mp2')


class MP3Scanner:
	def __init__(self):
		self.lastScanned=0
		self.scannedDirs=[]
		self.goodFiles={}		# dictionary of  dir --> list of (file, ID3)
		self.skippedFiles={}	# dictionary of  dir --> files
		self.clearCache()
		
	def clearCache(self):
		self._cache_filter_artist=None
		self._cache_filter_genre=None
		self._cache_filter_title=None
		self._cache_filter_file=None
		self._cache_filter_year=None
		self._cache_filter_album=None

	def readFromDisk(self, file):
		self.clearCache()
		(self.lastScanned, self.scannedDirs, self.goodFiles, self.skippedFiles) = pickle.load( open(file,'rb') )
		
	def writeToDisk(self, file):
		pickle.dump( (self.lastScanned, self.scannedDirs, self.goodFiles, self.skippedFiles) , open(file,'wb') ,1 )

	def walkfunc(self, arg, d, files):
		os.chdir(d)
		print 'Scanning',d

		_good = []
		_skipped=[]

		for f in files:
			if not os.path.isdir(f):
				suffix=os.path.splitext(f)[1].lower()
				if suffix in suffixes:
					try:
						id = ID3(f)
						_good.append((f,id))
					except (NoTagFoundError),x:
						_good.append((f,None))
					except Exception,x:
						print 'Error during scan of',os.path.join(d,f)
						print '    The error was:',x
				else:
					_skipped.append(f)

		if _good:
			self.goodFiles[d]=_good
		if _skipped:
			self.skippedFiles[d]=_skipped

	def scan(self, dir):
		self.clearCache()
		root=os.path.abspath(dir)
		if os.access(root, os.R_OK):
			currentdir = os.getcwd()
			os.path.walk(root,self.walkfunc,None)
			os.chdir(currentdir)
			self.lastScanned = int(time.time())
			self.scannedDirs.append(dir)
		else:
			raise IOError("cannot scan directory "+dir)

	def filterByFile(self):
		if self._cache_filter_file:
			return self._cache_filter_file
		else:
			result={}
			for(d,files) in self.getAllMP3dirs().items():
				for file in files:
					result.setdefault(file[0],[]).append( (d,file[0],file[1]) )
			self._cache_filter_file=result
			return result
			
	def filterByTitle(self):
		if self._cache_filter_title:
			return self._cache_filter_title
		else:
			result={}
			for(d,files) in self.getAllMP3dirs().items():
				for file in files:
					if file[1] and file[1].title:
						title=file[1].title
					else:
						title="{unknown}"
					result.setdefault(title,[]).append( (d,file[0],file[1]) )
			self._cache_filter_title=result
			return result

	def filterByArtist(self):
		if self._cache_filter_artist:
			return self._cache_filter_artist
		else:
			result={}
			for(d,files) in self.getAllMP3dirs().items():
				for file in files:
					if file[1] and file[1].artist:
						artist=file[1].artist
					else:
						artist="{unknown}"
					result.setdefault(artist,[]).append( (d,file[0],file[1]) )
			self._cache_filter_artist=result
			return result

	def filterByAlbum(self):
		if self._cache_filter_album:
			return self._cache_filter_album
		else:
			result={}
			for(d,files) in self.getAllMP3dirs().items():
				for file in files:
					if file[1] and file[1].album:
						album=file[1].album
					else:
						album="{unknown}"
					result.setdefault(album,[]).append( (d,file[0],file[1]) )
			self._cache_filter_album=result
			return result

	def filterByYear(self):
		if self._cache_filter_year:
			return self._cache_filter_year
		else:
			result={}
			for(d,files) in self.getAllMP3dirs().items():
				for file in files:
					year=9999
					if file[1]:
						try:
							year=int(file[1].year)
						except ValueError:
							pass
					result.setdefault(year,[]).append( (d,file[0],file[1]) )
			self._cache_filter_year=result
			return result

	def filterByGenre(self):
		if self._cache_filter_genre:
			return self._cache_filter_genre
		else:
			result={}
			for(d,files) in self.getAllMP3dirs().items():
				for file in files:
					genre="{?}"
					if file[1]:
						genreidx=file[1].genre
						if genreidx>=0 and genreidx<len(genres):
							genre=genres[genreidx]
					result.setdefault(genre,[]).append( (d,file[0],file[1]) )
			self._cache_filter_genre=result
			return result

	def getAllMP3dirs(self):
		return self.goodFiles
	def getAllNonMP3(self):
		return self.skippedFiles
	def getTotalMP3FileCount(self):
		length=0
		for (d,files) in self.getAllMP3dirs().items():
			length+=len(files)
		return length
	def getByFileID(self, searchid):
		for (d,files) in self.getAllMP3dirs().items():
			for (file,id3) in files:
				if id(file)==searchid:
					return (d,file,id3)
		return None
	def getByDirID(self, searchid):
		result = []
		for (d,files) in self.getAllMP3dirs().items():
			if id(d)==searchid:
				for (file,id3) in files:
					result.append ((d,file, id3))
		return result


def printList(lst):
	for (d,files) in lst.items():
		print d
		for f in files:
			print '   ',f

def printTagsList(lst):
	for (d,files) in lst.items():
		print d
		for f in files:
			print f[1]


def printHTMLlist(out, list):
	print >>out, "<table border=1>"
	keys=list.keys()
	keys.sort()
	for name in keys:
		items=list[name]
		print >>out, "<tr><td valign=top rowspan=%d>%s" % (len(items)+1, name)
		for (dir,file,id3) in items:
			if id3:
				id3txt = "ID3"
			else:
				id3txt = "-"
			print >>out, "<td>%s<td>%s<td>%s<td>%lx" % ( dir, file, id3txt, id(file))
			print >>out, "<tr>"
	print >>out, "</table>"

	
