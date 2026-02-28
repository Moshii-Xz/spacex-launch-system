data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../lambda"
  output_path = "${path.root}/../lambda/dist/function.zip"
  excludes    = ["tests", "__pycache__", "*.pyc", "dist"]
}

resource "aws_lambda_function" "spacex_collector" {
  function_name    = "${var.lambda_function_name}-${var.environment}"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = var.lambda_runtime
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.spacex_launches.name
      ENVIRONMENT    = var.environment
      LOG_LEVEL      = "INFO"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_dynamo_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# Log group para la Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.lambda_function_name}-${var.environment}"
  retention_in_days = 30
}

# EventBridge rule para ejecución cada 6 horas
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "${var.lambda_function_name}-schedule-${var.environment}"
  description         = "Ejecuta la Lambda de SpaceX cada 6 horas"
  schedule_expression = var.lambda_schedule_expression
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "SpaceXCollectorLambda"
  arn       = aws_lambda_function.spacex_collector.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spacex_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}

# API Gateway para invocación manual
resource "aws_apigatewayv2_api" "lambda_api" {
  name          = "${var.lambda_function_name}-api-${var.environment}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "lambda_stage" {
  api_id      = aws_apigatewayv2_api.lambda_api.id
  name        = var.environment
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.lambda_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.spacex_collector.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "trigger_route" {
  api_id    = aws_apigatewayv2_api.lambda_api.id
  route_key = "POST /trigger"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spacex_collector.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.lambda_api.execution_arn}/*/*"
}
