FileMgr - web-based file managing system.
(written as a web application for Snakelets)


This software is copyright © by Irmen de Jong.

This software is released under the GNU General Public License (GPL),
which can be found in the 'LICENSE' file.
(some modules may have another license, that is clearly
marked in the source of those modules).


Please give me credit if you use this software.

INSTALLATION:
-------------
Copy the 'filemgr' webapp to the webapps folder of your Snakelets 
installation. Edit the webapp's init file to change the required
configuration parameters (they're fairly self explanatory).
You can use the 'mkuser.py' script to add new users.
If you use Frog (see below), and you have the SharedAuth plugin,
the filemgr will use Frog's user auth so that you don't have to
duplicate Frog's users here.

Start Snakelets, and open the index page in your browser :)
(http://server:port/filemgr/)

Frog:
-----
This file manager application is specially designed to work very
well with Frog (my web log application). Actually, Frog links
to this file manager by default from the menu :-)
(and implements shared authentication for filemgr)

----------

Irmen de Jong
irmen@users.sourceforge.net

