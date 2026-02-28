resource "aws_dynamodb_table" "spacex_launches" {
  name         = "${var.dynamodb_table_name}-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "launch_id"

  attribute {
    name = "launch_id"
    type = "S"
  }

  attribute {
    name = "launch_date"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # GSI para consultar por fecha
  global_secondary_index {
    name            = "launch_date-index"
    hash_key        = "launch_date"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.dynamodb_table_name}-${var.environment}"
  }
}
