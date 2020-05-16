resource "aws_api_gateway_rest_api" "budget" {
  name = "budget"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "v1" {
  depends_on  = [aws_api_gateway_integration.monzo_lambda]
  rest_api_id = "${aws_api_gateway_rest_api.budget.id}"
}

resource "aws_api_gateway_stage" "v1" {
  stage_name    = "v1"
  rest_api_id   = "${aws_api_gateway_rest_api.budget.id}"
  deployment_id = "${aws_api_gateway_deployment.v1.id}"
}

resource "aws_api_gateway_resource" "monzo" {
  rest_api_id = "${aws_api_gateway_rest_api.budget.id}"
  parent_id   = "${aws_api_gateway_rest_api.budget.root_resource_id}"
  path_part   = "monzo"
}

resource "aws_api_gateway_method" "monzo" {
  rest_api_id   = "${aws_api_gateway_rest_api.budget.id}"
  resource_id   = "${aws_api_gateway_resource.monzo.id}"
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "ok" {
  rest_api_id = "${aws_api_gateway_rest_api.budget.id}"
  resource_id = "${aws_api_gateway_resource.monzo.id}"
  http_method = "${aws_api_gateway_method.monzo.http_method}"
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "ok" {
  depends_on  = [aws_api_gateway_integration.monzo_lambda]
  rest_api_id = "${aws_api_gateway_rest_api.budget.id}"
  resource_id = "${aws_api_gateway_resource.monzo.id}"
  http_method = "${aws_api_gateway_method.monzo.http_method}"
  status_code = "${aws_api_gateway_method_response.ok.status_code}"

  response_templates = {
    "application/json" = ""
  }
}

resource "aws_api_gateway_integration" "monzo_lambda" {
  rest_api_id = "${aws_api_gateway_rest_api.budget.id}"
  resource_id = "${aws_api_gateway_method.monzo.resource_id}"
  http_method = "${aws_api_gateway_method.monzo.http_method}"
  uri         = "${aws_lambda_function.monzo_webhook.invoke_arn}"

  integration_http_method = "POST"
  type                    = "AWS"
  content_handling        = "CONVERT_TO_TEXT"
  passthrough_behavior    = "WHEN_NO_MATCH"
}

resource "aws_lambda_permission" "api_lambda" {
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.monzo_webhook.function_name}"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.budget.execution_arn}/*/${aws_api_gateway_method.monzo.http_method}${aws_api_gateway_resource.monzo.path}"
}
