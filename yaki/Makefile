all:
	@echo "This makefile is only for cleaning stuff up. ('make clean')"

run: minify
	python app.py

minify:
	@echo "Minifying CSS"
	cd webapps/ROOT/web/themes/k2/css/src ; sh minify.sh
	@echo "Minifying JS"
	cd webapps/ROOT/web/themes/k2/js/src ; sh minify.sh

clean:
	@echo "Removing stray logfiles, .pyo/.pyc files..."
	find . -name \*.pyo | xargs rm
	find . -name \*.pyc | xargs rm
	find . -name \*.swp | xargs rm
	find . -name \*~ | xargs rm
	find . -name \*_log | xargs rm
	find . -name \*.log | xargs rm
	find . -name \*.log.? | xargs rm
	find . -name \*.log.?? | xargs rm
	@echo "Removing non-CVS files..."
	rm -fv MANIFEST 
	rm -rf build
	rm -rf logs/server.pid
	find . -name  .#\* | xargs rm
	@echo "clean!"


