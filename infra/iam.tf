# ─── ROL PARA LAMBDA ─────────────────────────────────────────────────────────

resource "aws_iam_role" "lambda_exec" {
  name = "${var.lambda_function_name}-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "lambda_dynamo" {
  name        = "${var.lambda_function_name}-dynamo-policy-${var.environment}"
  description = "Permite a la Lambda leer y escribir en DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query",
        "dynamodb:BatchWriteItem"
      ]
      Resource = [
        aws_dynamodb_table.spacex_launches.arn,
        "${aws_dynamodb_table.spacex_launches.arn}/index/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamo_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_dynamo.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ─── ROL PARA ECS TASK EXECUTION ─────────────────────────────────────────────

resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.ecs_service_name}-exec-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ─── ROL PARA ECS TASK (acceso a DynamoDB desde la app) ──────────────────────

resource "aws_iam_role" "ecs_task" {
  name = "${var.ecs_service_name}-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "ecs_dynamo_read" {
  name        = "${var.ecs_service_name}-dynamo-read-${var.environment}"
  description = "Permite a la app web leer datos de DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ]
      Resource = [
        aws_dynamodb_table.spacex_launches.arn,
        "${aws_dynamodb_table.spacex_launches.arn}/index/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_dynamo_read_policy" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_dynamo_read.arn
}
