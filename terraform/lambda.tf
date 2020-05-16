resource "aws_lambda_function" "monzo_webhook" {
  function_name = "monzo-webhook"
  role          = aws_iam_role.monzo_lambda.arn

  filename         = var.lambda_package
  source_code_hash = filebase64sha256(var.lambda_package)
  handler          = "monzo-webhook.lambda_handler"
  memory_size      = "128"
  runtime          = "python3.6"
  timeout          = "11"

  environment {
    variables = {
      AUTHCREDS      = "gsheets.json"
      SPREADSHEET_ID = ""
      WORKSHEET      = ""
    }
  }
}
