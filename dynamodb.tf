resource "aws_dynamodb_table" "payment_ledger" {
  name           = "${var.dynamodb_table_name}-Ledger"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  # Enable Point-in-Time Recovery (PITR)
  point_in_time_recovery {
    enabled = true
  }

  hash_key = "TransactionID"

  # Attributes for the Payment Ledger table
  attribute {
    name = "TransactionID"
    type = "S"
  }

  attribute {
    name = "TransactionType"
    type = "S"
  }

  attribute {
    name = "Source"
    type = "S"
  }

  attribute {
    name = "Amount"
    type = "N"
  }

  attribute {
    name = "Currency"
    type = "S"
  }

  attribute {
    name = "ProcessorID"
    type = "S"
  }

  attribute {
    name = "Status"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "S"
  }

  attribute {
    name = "Initiator"
    type = "S"
  }

  attribute {
    name = "Reason"
    type = "S"
  }

  attribute {
    name = "Metadata"
    type = "S"
  }

  attribute {
    name = "UserID"
    type = "S"
  }

  attribute {
    name = "Environment"
    type = "S"
  }

  # Global Secondary Indexes for querying by attributes that need indexing
  global_secondary_index {
    name            = "TransactionType-index"
    hash_key        = "TransactionType"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Status-index"
    hash_key        = "Status"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Source-index"
    hash_key        = "Source"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Timestamp-index"
    hash_key        = "Timestamp"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "UserID-index"
    hash_key        = "UserID"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Environment-index"
    hash_key        = "Environment"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  tags = {
    Name = "${var.dynamodb_table_name}-ledger"
  }
}

resource "aws_dynamodb_table" "payment_audit_trail" {
  name           = "${var.dynamodb_table_name}-AuditTrail"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  # Enable Point-in-Time Recovery (PITR)
  point_in_time_recovery {
    enabled = true
  }

  hash_key = "AuditID"

  # Attributes for the Payment Audit Trail table
  attribute {
    name = "AuditID"
    type = "S"
  }

  attribute {
    name = "TransactionID"
    type = "S"
  }

  attribute {
    name = "TransactionType"
    type = "S"
  }

  attribute {
    name = "Source"
    type = "S"
  }

  attribute {
    name = "Action"
    type = "S"
  }

  attribute {
    name = "Status"
    type = "S"
  }

  attribute {
    name = "Amount"
    type = "N"
  }

  attribute {
    name = "Currency"
    type = "S"
  }

  attribute {
    name = "Reason"
    type = "S"
  }

  attribute {
    name = "Initiator"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "S"
  }

  attribute {
    name = "Metadata"
    type = "S"
  }

  attribute {
    name = "UserID"
    type = "S"
  }

  attribute {
    name = "ProcessorResponse"
    type = "S"
  }

  attribute {
    name = "IPAddress"
    type = "S"
  }

  attribute {
    name = "Environment"
    type = "S"
  }

  # Global Secondary Indexes (GSI)
  global_secondary_index {
    name            = "TransactionID-Action-index"
    hash_key        = "TransactionID"
    range_key       = "Action"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "TransactionType-index"
    hash_key        = "TransactionType"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Source-index"
    hash_key        = "Source"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Status-index"
    hash_key        = "Status"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "UserID-index"
    hash_key        = "UserID"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  global_secondary_index {
    name            = "Environment-index"
    hash_key        = "Environment"
    projection_type = "ALL"
    read_capacity   = 5
    write_capacity  = 5
  }

  tags = {
    Name = "${var.dynamodb_table_name}-audit-trail"
  }
}
