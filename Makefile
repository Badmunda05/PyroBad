RM := rm -rf
HOST = $(shell ifconfig | grep "inet " | tail -1 | cut -d\  -f2)
TAG = v$(shell awk -F'"' '/^__version__ = /{print $$2}' pyrogram/__init__.py)

.PHONY: clean-build clean-api clean-docs clean api docs build

clean-build:
	$(RM) *.egg-info build dist

clean-api:
	$(RM) pyrogram/errors/exceptions pyrogram/raw/all.py pyrogram/raw/base pyrogram/raw/functions pyrogram/raw/types

clean-docs:
	$(RM) docs/build docs/source/api/bound-methods docs/source/api/methods docs/source/api/types docs/source/api/enums docs/source/telegram

clean:
	make clean-build
	make clean-api
	make clean-docs

api:
	cd compiler/api && python compiler.py
	cd compiler/errors && python compiler.py

# How to build docs locally:
# pip install Sphinx,sphinx_copybutton,furo
# pip uninstall kurigram pyrogram -y && pip install --force-reinstall file:.
# make clean api docs
docs:
	cd compiler/docs && python compiler.py
	sphinx-build -b dirhtml "docs/source" "docs/build/html" -j auto

build:
	make clean
	python setup.py sdist
	python setup.py bdist_wheel

tag:
	git tag $(TAG)
	git push origin $(TAG)

dtag:
	git tag -d $(TAG)
	git push origin -d $(TAG)
