
all:	_selkie_dev _js

_selkie_dev:
	python -m venv _selkie_dev
	source _selkie_dev/bin/activate; pip install --upgrade pip
	source _selkie_dev/bin/activate; cd ..; pip install -e .
	source _selkie_dev/bin/activate; pip install sphinx python_docs_theme tornado jupyter

_js:
	mkdir _js
	cd _js; npm install create-react-app; npx create-react-app app
	rm -rf _js/app/src/*
	cp ../src/selkie/js/* _js/app/src
	cd _js/app; npm run build

#	_js/app/package.json - added  "homepage": "/build/"
#	Edited _js/app/src/App.js

docs:
	cd ../docs; make html

viewdocs:
	open ../docs/_build/html

pristine:
	rm -rf _env _js
