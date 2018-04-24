LAMBDA_FUNCTION_NAME=monzo-webhook
LAMBDA_HANDLER=newTransaction
LAMBDA_FILE=$(LAMBDA_FUNCTION_NAME).py
ZIP_FILE=$(LAMBDA_FUNCTION_NAME).zip
PACKAGE_ZIP=dist/$(ZIP_FILE)
VIRT_ENV=env
LAMBDA_ENV=config/lambda.env
LAMBDA_ROLE=arn:aws:iam::CHANGEME:role/..

install: venv
build: mkdist clean_dist zip
update: build lambda_upload lambda_setenv

venv:
	if test ! -d "$(VIRT_ENV)"; then \
		pip3 install virtualenv; \
		virtualenv $(VIRT_ENV); \
	fi
	( \
		. $(VIRT_ENV)/bin/activate; \
		pip3 install -r config/requirements.txt; \
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
	cp -r src/* dist/

zip:
	cd dist; \
		chmod 644 $(LAMBDA_FILE); \
		zip -r $(ZIP_FILE) *; \
		chmod 644 $(ZIP_FILE); \

lambda_upload:
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$(PACKAGE_ZIP)

lambda_setenv:
	aws lambda update-function-configuration \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--environment Variables="{"$(shell cat $(LAMBDA_ENV) | paste -sd',' -)"}"

lambda_create:
	aws lambda create-function \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--runtime python3.6 \
		--role $(LAMBDA_ROLE) \
		--handler $(LAMBDA_FUNCTION_NAME).$(LAMBDA_HANDLER) \
		--zip-file fileb://$(PACKAGE_ZIP) \
		--environment Variables="{"$(shell cat $(LAMBDA_ENV) | paste -sd',' -)"}" \
		--timeout 8 \
		--memory-size 128 \

lambda_delete:
	aws lambda delete-function \
		--function-name $(LAMBDA_FUNCTION_NAME)
