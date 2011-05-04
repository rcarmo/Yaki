# configuration for this webapp

import music
import streamer

name="Music browser"
docroot="."

snakelets= {
	"music.sn": music.Music,
	"stream.m3u": music.Playlist,
	"streamer.sn": streamer.Streamer
	}


# custom config items:
configItems = {
	# "stream_url_base": "http://hostname:3333",     # use this to override mp3 player stream URL base
	
	"max_results": 200
}
	
