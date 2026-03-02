output "dynamodb_table_name" {
  description = "Nombre de la tabla DynamoDB"
  value       = aws_dynamodb_table.spacex_launches.name
}

output "dynamodb_table_arn" {
  description = "ARN de la tabla DynamoDB"
  value       = aws_dynamodb_table.spacex_launches.arn
}

output "lambda_function_name" {
  description = "Nombre de la función Lambda"
  value       = aws_lambda_function.spacex_collector.function_name
}

output "lambda_function_arn" {
  description = "ARN de la función Lambda"
  value       = aws_lambda_function.spacex_collector.arn
}

output "api_gateway_url" {
  description = "URL del endpoint para invocar la Lambda manualmente"
  value       = "${aws_apigatewayv2_stage.lambda_stage.invoke_url}/trigger"
}

output "ecr_repository_url" {
  description = "URL del repositorio ECR (webapp)"
  value       = aws_ecr_repository.webapp.repository_url
}

output "ecr_backend_repository_url" {
  description = "URL del repositorio ECR (backend API)"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "Nombre del cluster ECS"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Nombre del servicio ECS (webapp)"
  value       = aws_ecs_service.webapp.name
}

output "ecs_backend_service_name" {
  description = "Nombre del servicio ECS (backend API)"
  value       = aws_ecs_service.backend.name
}

output "alb_dns_name" {
  description = "DNS del Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "webapp_url" {
  description = "URL pública de la webapp (vía ALB — DNS estable)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "api_url" {
  description = "URL base de la API REST (vía ALB)"
  value       = "http://${aws_lb.main.dns_name}/api/v1"
}

output "swagger_url" {
  description = "URL del Swagger UI (vía ALB)"
  value       = "http://${aws_lb.main.dns_name}/docs"
}
