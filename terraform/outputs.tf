data "aws_region" "current" {}

output "endpoint" {
  value = "${aws_api_gateway_stage.v1.invoke_url}${aws_api_gateway_resource.monzo.path}"
}
