LAMBDA_FUNCTION_NAME=monzo-webhook
LAMBDA_HANDLER=newTransaction
LAMBDA_FILE=monzo.py
ZIP_FILE=monzo.zip
PACKAGE_ZIP=dist/$(ZIP_FILE)
VIRT_ENV=env
include lambda.env 	# provides AUTHCREDS

install: venv
build: mkdist clean_dist zip
update: build upload set_env

venv:
	if test ! -d "$(VIRT_ENV)"; then \
		pip3 install virtualenv; \
		virtualenv $(VIRT_ENV); \
	fi
	( \
		. $(VIRT_ENV)/bin/activate; \
		pip3 install -r requirements.txt; \
	)

clean_dist:
	rm -fr dist/*.dist-info
	rm -fr dist/*.egg-info
	cd dist; \
		rm -fr __pycache__; \
		rm -fr easy_install.py; \
		rm -fr pip; \
		rm -fr pkg_resources; \
		rm -fr setuptools; \
		rm -fr wheel; \

mkdist:
	mkdir -p dist
	cp -r $(VIRT_ENV)/lib/python3*/site-packages/* dist/
	cp $(LAMBDA_FILE) dist/
	cp $(AUTHCREDS) dist/

zip:
	cd dist; \
		chmod 644 $(LAMBDA_FILE); \
		zip -r $(ZIP_FILE) *; \
		chmod 644 $(ZIP_FILE); \

upload:
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$(PACKAGE_ZIP)

set_env:
	aws lambda update-function-configuration \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--environment Variables="{"$(shell cat lambda.env | paste -sd',' -)"}"
