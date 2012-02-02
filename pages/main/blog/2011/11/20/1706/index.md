From: Rui Carmo
Date: 2011-11-20 17:06:58
Title: Bootstrapping
Tags: yaki, relnotes

Finally had time to merge a number of disparate instances' source together into a cohesive whole.

Right now, the Github source tree is (save minor tweaks) at least one month _ahead_ of the [Tao][t] feature-wise, which is a first.

## What's new

To make it easier for people to get up and running, I've stabilized the master branch and re-arranged the filesystem layout somewhat, and made a few more changes:

* [Twitter Bootstrap][tb] is now the `ROOT` instance theme (the `minimal` theme is, well, too minimal)
* Updated some dependencies in `userlib` (mostly [Whoosh][w])
* Added multiple template support (each page can now specify its own template, provided you add the appropriate `.y` file to your theme folder)
* Removed just about every `print` statement I saw and changed it to proper `logging` calls (there are a few dotted here and there still, but I'll get to them eventually).

## Known issues

The multiple wiki instance code is not quite ready yet. You can deploy and navigate multiple wikis and most of the back-end and rendering will work fine, but some things (for instance, searches) will only work properly on the `ROOT` instance.

## In need of testing

* Thumbnailing
* Font previewing

## In need of further tweaking

Bootstrap itself. I'm not quite happy with the typography and layout for some reason. Also, docs.

[tb]: http://twitter.github.com/bootstrap/
[t]: http://the.taoofmac.com
[w]: Whoosh
