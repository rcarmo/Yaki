# Yaki - A fast, powerful filesystem-based wiki

## About

This is the second public release of Yaki (the first was in [Google Code][gc], and is long obsolete).

Yaki is a filesystem-based wiki that is used as the underpinnings of [The Tao of Mac][t] (and a few other sites that started using the initial release).

## Features

* 100% pure Python, with extensive UTF-8 support
* Entirely self-hosting, running atop a modified Snakelets application framework
* Completely filesystem-based (pages are stored on a directory structure, not a database)
* Heavily optimized HTTP processing:
    * Pages are pre-processed to HTML 
    * HTML and other internal info are stored in a single-file cache, _a la_ [Haystack](http://www.facebook.com/note.php?note_id=76191543919)
    * Everything is served via `sendfile(2)` calls whenever possible
    * Uses every HTTP caching trick in the book to minimize actual page hits
* Completely markup-agnostic - all the internal processing relies on Beautiful Soup, and it ships with support for:
    * raw HTML
    * Textile
    * Markdown
* Any markup engine that generates HTML can be added, and markup can be defined on a site-wide or page-per-page basis
* Has all the usual features, like:
    * Page aliasing
    * Interwiki
    * RecentChanges
    * etc.
* Has a number of unusual Bliki features, like a blog-like home page, linkblog support, and the SeeAlso table at the bottom of each page.
* Supports full-text indexing and search using [Whoosh](http://bitbucket.org/mchaput/whoosh/wiki/Home)

## Requirements

* Python 2.6 (2.7 will work just as well, and 2.5 may work with minimal tweaks)
* That's it.

## License

Yaki is released under the [MIT License][mit]. Some third-party libraries in the `userlibs` folder are licensed differently and are included merely to ease deployment.

The [Twitter Bootstrap][tb] HTML+CSS which is now used as the default theme is licensed under the [Apache License v2.0][al].

## Credits

The Snakelets application server was originally developed by [Irmen de Jong][i], and as far as I know this is the only publicly maintained version of it.

[mit]: http://www.opensource.org/licenses/mit-license.php
[tb]: http://twitter.github.com/bootstrap/
[al]: http://www.apache.org/licenses/LICENSE-2.0
[gc]: http://code.google.com/p/yaki/
[t]: http://the.taoofmac.com
[i]: http://www.razorvine.net/