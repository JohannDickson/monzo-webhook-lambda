data "aws_region" "current" {}

output "endpoint" {
  value = "https://${aws_api_gateway_rest_api.budget.id}.execute-api.${data.aws_region.current.name}.amazonaws.com${aws_api_gateway_resource.monzo.path}"
}
