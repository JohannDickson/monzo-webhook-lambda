## Pre-requisites

In order to run this deployment you will need:
- Python 3
- Terraform 0.12
- An AWS account with your [local credentials set](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- A [Google sheet](sheets.new) in which to insert the data
- A [Service account]() with Edit permissions on the above sheet


## Creating the Service Account

- Log in to the [developer console](https://console.developers.google.com/)
- Create a new project
- Enable the [Google Sheets API](https://console.developers.google.com/apis/library/sheets.googleapis.com)
- Navigate to [Credentials](https://console.developers.google.com/apis/api/sheets.googleapis.com/credentials) and create a new Service Account
- Give it the name and description you want
- Leave the role blank
- Create a new key (JSON)
- This will automatically download the credentials file, rename it locally to `gsheets.json` and move it into the `src` directory
- In your sheet, share access with the service account's Email as an Editor


## Building the Lambda bundle

From the root of this repository, run the following commands to install all required dependencies and create the packaged zip that we'll upload to AWS.
```
make install
make build
```


## Deploying the infrastructure

Navigate into the `terraform` directory and run the following:
```
terraform init
terraform apply
```

This will deploy:
- the lambda itself
- a basic IAM role for the lambda (write to cloudwatch logs)
- an API gateway with a single route/method and lambda integration

Terraform will output the URL to be registered with the Monzo API.
You can also retrieve it later by running `terraform output endpoint`


## Registering your webhook with Monzo

With the URL output from the previous section,
- Make your way to the [Monzo developers](https://developers.monzo.com/) page
- Go to "Register webhook" and replace the url in the textbox with yours, click Send
- You can validate by running the "List webhooks" action
