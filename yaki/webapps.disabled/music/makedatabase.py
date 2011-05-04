#! /usr/bin/env python
#
#	Re-create the pickled mp3 database (the MP3Scanner object)
#

from mp3.mp3tool import MP3Scanner

import sys

if len(sys.argv)>=2:
	scanner=MP3Scanner()
	
	for path in sys.argv[1:]:
		scanner.scan(path)
		
	scanner.writeToDisk("database.bin")
	print "binary database written to 'database.bin'"
else:
	print "Give one or more paths to scan as arguments."
