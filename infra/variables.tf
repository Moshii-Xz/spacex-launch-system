variable "aws_region" {
  description = "Región de AWS donde se despliegan los recursos"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Entorno de despliegue (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "spacex-launch-system"
}

variable "dynamodb_table_name" {
  description = "Nombre de la tabla DynamoDB"
  type        = string
  default     = "spacex-launches"
}

variable "lambda_function_name" {
  description = "Nombre de la función Lambda"
  type        = string
  default     = "spacex-data-collector"
}

variable "lambda_runtime" {
  description = "Runtime de la función Lambda"
  type        = string
  default     = "python3.11"
}

variable "lambda_schedule_expression" {
  description = "Expresión cron para la ejecución automática (cada 6 horas)"
  type        = string
  default     = "rate(6 hours)"
}

variable "ecr_repository_name" {
  description = "Nombre del repositorio ECR"
  type        = string
  default     = "spacex-webapp"
}

variable "ecs_cluster_name" {
  description = "Nombre del cluster ECS"
  type        = string
  default     = "spacex-cluster"
}

variable "ecs_service_name" {
  description = "Nombre del servicio ECS"
  type        = string
  default     = "spacex-webapp-service"
}

variable "ecs_task_cpu" {
  description = "CPU asignada a la tarea ECS (en unidades)"
  type        = string
  default     = "256"
}

variable "ecs_task_memory" {
  description = "Memoria asignada a la tarea ECS (en MB)"
  type        = string
  default     = "512"
}

variable "webapp_port" {
  description = "Puerto expuesto por la aplicación web"
  type        = number
  default     = 80
}
