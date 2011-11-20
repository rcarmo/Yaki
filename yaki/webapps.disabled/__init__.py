# virtual host configuration


#
#	FIRST USE NOTICE:
#	YOU HAVE TO CONFIGURE THIS FILE FOR YOUR OWN SYSTEM;
#	CHANGE vhostname TO THE CORRECT HOSTNAME THAT MUST BE USED.
#	(OR CONFIGURE IT TO YOUR OWN WISHES OFCOURSE)
#
#	THEN, ENABLE IT BY SETTING THE FLAG BELOW TO True.
#

ENABLED = False

# webapps that will be loaded for the default config (if vhosts is disabled)
# use ["*"] to enable all of them
defaultenabledwebapps=["*"]


# virtualhosts is a mapping of host names to a sequence of
# web application names that will be connected to the specified hostname. 
# If a web application is not mentioned for any virtual host,
# it will NOT be loaded. A web app may be connected to multiple vhosts.

virtualhosts = {
	"vhostname" : ("account", "manage", "music", "shop", "test", "shared1", "shared2")
}


# webroots is a mapping of host names to the name of the web app
# that will be mapped in the URL root ( '/' ) of the server on
# that virtual host. The host names MUST correspond to the host names
# from the virtualhosts mapping above.

webroots = {
	"vhostname" : "ROOT"
}

# aliases is a mapping of vhost-alias name to real-vhost name.
# (this avoids duplicate loading of webapps)

aliases= {}

# defaultvhost is the name of the default virtual host
# (specified above) that will be used when the browser
# doesn't send a Host header.


defaultvhost = "vhostname"

