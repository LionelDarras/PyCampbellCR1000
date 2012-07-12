SHELL := /bin/bash

# these files should pass pyflakes
# exclude ./env/, which may contain virtualenv packages
PYFLAKES_WHITELIST=$(shell find . -name "*.py" ! -path "./docs/*" \
                    ! -path "./.tox/*" ! -path "./pycampbellcrx/__init__.py" \
                    ! -path "./pycampbellcrx/compat.py" ! -path "./env/*")

env:
	rm ./env -fr
	virtualenv ./env
	/bin/bash -c 'source ./env/bin/activate ; pip install pep8 ; \
    pip install pyflakes ; \
    pip install tox ; pip install -e . '

test:
	tox

pyflakes:
	pyflakes ${PYFLAKES_WHITELIST}

pep:
	pep8 pycampbellcrx

doc:
	cd docs; make html

clean:
	git clean -Xfd

dist:
	python setup.py sdist

upload:
	python setup.py sdist upload

