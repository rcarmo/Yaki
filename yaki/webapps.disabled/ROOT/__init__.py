# configuration for this webapp

name="Web server root"

docroot="."

snakelets={}

def dirListAllower(path):
	# path will be RELATIVE for this webapp, and NOT starting with /

	# this (root)webapp allows ALL dirs to be viewed
	return True
