data "aws_caller_identity" "current" {}
data "aws_vpc" "default" { default = true }
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ─── ECR ─────────────────────────────────────────────────────────────────────

resource "aws_ecr_repository" "webapp" {
  name                 = "${var.ecr_repository_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "backend" {
  name                 = "spacex-backend-${var.environment}"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

# ─── ECS CLUSTER ─────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = "${var.ecs_cluster_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ─── LOG GROUPS ──────────────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${var.ecs_service_name}-${var.environment}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "backend_logs" {
  name              = "/ecs/spacex-backend-${var.environment}"
  retention_in_days = 30
}

# ─── SECURITY GROUP — ALB ────────────────────────────────────────────────────

resource "aws_security_group" "alb_sg" {
  name        = "spacex-alb-sg-${var.environment}"
  description = "Security group para el Application Load Balancer"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "spacex-alb-sg-${var.environment}" }
}

# ─── SECURITY GROUPS — ECS (acepta tráfico solo desde el ALB) ────────────────

resource "aws_security_group" "ecs_sg" {
  name        = "${var.ecs_service_name}-sg-${var.environment}"
  description = "Security group para ECS Fargate webapp"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "HTTP traffic from ALB"
    from_port       = var.webapp_port
    to_port         = var.webapp_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.ecs_service_name}-sg-${var.environment}" }
}

resource "aws_security_group" "backend_sg" {
  name        = "spacex-backend-sg-${var.environment}"
  description = "Security group para ECS Fargate backend API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "API traffic from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "spacex-backend-sg-${var.environment}" }
}

# ─── APPLICATION LOAD BALANCER ───────────────────────────────────────────────

resource "aws_lb" "main" {
  name               = "spacex-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.public.ids

  enable_deletion_protection = false

  tags = { Name = "spacex-alb-${var.environment}" }
}

# ─── TARGET GROUPS ───────────────────────────────────────────────────────────

resource "aws_lb_target_group" "webapp" {
  name        = "spacex-webapp-tg-${var.environment}"
  port        = var.webapp_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  deregistration_delay = 30

  tags = { Name = "spacex-webapp-tg-${var.environment}" }
}

resource "aws_lb_target_group" "backend" {
  name        = "spacex-backend-tg-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  deregistration_delay = 30

  tags = { Name = "spacex-backend-tg-${var.environment}" }
}

# ─── ALB LISTENERS & RULES ───────────────────────────────────────────────────

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Acción por defecto: webapp
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webapp.arn
  }
}

# Regla: /api/v1/* → backend
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  condition {
    path_pattern {
      values = ["/api/v1*"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# Regla: /health → backend (para el health check del backend)
resource "aws_lb_listener_rule" "health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 90

  condition {
    path_pattern {
      values = ["/health"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# Regla: /docs y /openapi.json → backend (Swagger UI)
resource "aws_lb_listener_rule" "docs" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 80

  condition {
    path_pattern {
      values = ["/docs", "/docs/*", "/openapi.json", "/redoc"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# ─── TASK DEFINITIONS ────────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "webapp" {
  family                   = "${var.ecs_service_name}-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "webapp"
    image = "${aws_ecr_repository.webapp.repository_url}:latest"
    portMappings = [{
      containerPort = var.webapp_port
      protocol      = "tcp"
    }]
    environment = [
      { name = "ENVIRONMENT", value = var.environment }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "spacex-backend-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "DYNAMODB_TABLE",       value = aws_dynamodb_table.spacex_launches.name },
      { name = "AWS_REGION",           value = var.aws_region },
      { name = "ENVIRONMENT",          value = var.environment },
      { name = "LAMBDA_FUNCTION_NAME", value = "${var.lambda_function_name}-${var.environment}" },
      { name = "CORS_ORIGINS",         value = "*" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend_logs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ─── ECS SERVICES ────────────────────────────────────────────────────────────

resource "aws_ecs_service" "webapp" {
  name            = "${var.ecs_service_name}-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.webapp.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.webapp.arn
    container_name   = "webapp"
    container_port   = var.webapp_port
  }

  depends_on = [aws_lb_listener.http]
  lifecycle { ignore_changes = [task_definition] }
}

resource "aws_ecs_service" "backend" {
  name            = "spacex-backend-service-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.backend_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
  lifecycle { ignore_changes = [task_definition] }
}
