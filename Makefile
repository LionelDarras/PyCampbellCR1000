SHELL := /bin/bash

# these files should pass pyflakes
# exclude ./env/, which may contain virtualenv packages
PYFLAKES_WHITELIST=$(shell find . -name "*.py" ! -path "./docs/*" \
                    ! -path "./.tox/*" ! -path "./pycr1000/__init__.py" \
                    ! -path "./pycr1000/compat.py" ! -path "./env/*")

env:
	rm ./env -fr
	virtualenv ./env
	/bin/bash -c 'source ./env/bin/activate ; pip install pep8 ; \
        pip install pyflakes ; \
        pip install tox ; pip install -e . '

test_cr1000:
	tox -- -m cr1000

test_cr800:
	tox -- -m cr800

pyflakes:
	pyflakes ${PYFLAKES_WHITELIST}

pep:
	pep8 pycr1000

doc:
	cd docs; make html

clean:
	git clean -Xfd

dist:
	python setup.py sdist

upload:
	python setup.py sdist upload
