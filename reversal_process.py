import json
import boto3
import os
from datetime import datetime
from decimal import Decimal  # Import Decimal to handle DynamoDB's numeric fields

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")

# Fetch environment variables
TRANSACTION_TABLE = os.environ["TRANSACTION_TABLE"]  # Updated variable name
AUDIT_TRAIL_TABLE = os.environ["AUDIT_TRAIL_TABLE"]

def handler(event, context):
    try:
        # Log the incoming event for debugging
        print("Received event:", event)

        # Parse input
        body = json.loads(event["body"])
        print("Parsed body:", body)

        # Extract parameters
        transaction_id = body["TransactionID"]
        reversal_amount = Decimal(str(body["ReversalAmount"]))  # Convert float to Decimal
        reason = body.get("Reason", "No reason provided")
        initiator = body.get("Initiator", "System")
        print(f"TransactionID: {transaction_id}, ReversalAmount: {reversal_amount}, Reason: {reason}, Initiator: {initiator}")

        # Get reference to DynamoDB tables
        transaction_table = dynamodb.Table(TRANSACTION_TABLE)
        audit_table = dynamodb.Table(AUDIT_TRAIL_TABLE)

        # Fetch the original transaction from the TRANSACTION_TABLE
        original_transaction = transaction_table.get_item(Key={"TransactionID": transaction_id})
        print("Fetched original transaction:", original_transaction)

        if "Item" not in original_transaction:
            print("Transaction not found in the table")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Transaction not found"})
            }
        
        transaction = original_transaction["Item"]
        print("Transaction details:", transaction)

        # Step 2: Validate the transaction status and amount
        valid_statuses = ["completed", "success"]  # Lowercase valid statuses
        transaction_status = transaction["Status"].strip().lower()  # Convert to lowercase and strip any extra spaces
        transaction_type = transaction["TransactionType"].strip().lower()  # Transaction Type to validate the reversal

        if transaction_status not in valid_statuses:
            print(f"Transaction status is not eligible for reversal. Status: {transaction['Status']}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Transaction is not eligible for reversal"})
            }

        # Allow reversal only if it's a sale or specific types that can be reversed
        valid_transaction_types = ["sale", "charge", "refund"]  # Add your valid types
        if transaction_type not in valid_transaction_types:
            print(f"Transaction type {transaction_type} is not eligible for reversal.")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Transaction type is not eligible for reversal"})
            }

        original_amount = Decimal(str(transaction["Amount"]))  # Convert original transaction amount to Decimal

        if reversal_amount > original_amount:
            print("Reversal amount exceeds the original transaction amount.")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Reversal amount exceeds original transaction amount"})
            }

        # Step 3: Log the reversal attempt in the audit trail
        audit_id = f"audit-{datetime.utcnow().isoformat()}"
        audit_entry = {
            "AuditID": audit_id,
            "TransactionID": transaction_id,
            "Action": "REVERSAL",
            "Status": "PENDING",
            "TransactionType": transaction_type,  # Include the Transaction Type in the audit
            "Initiator": initiator,
            "Timestamp": datetime.utcnow().isoformat(),
            "Metadata": {
                "ReversalAmount": reversal_amount,
                "Reason": reason
            }
        }

        # Log the audit entry
        audit_table.put_item(Item=audit_entry)
        print("Audit entry created:", audit_entry)

        # Step 4: Update the original transaction status
        try:
            transaction_table.update_item(
                Key={"TransactionID": transaction_id},
                UpdateExpression="SET #s = :new_status, #t = :new_type",
                ExpressionAttributeNames={"#s": "Status", "#t": "TransactionType"},
                ExpressionAttributeValues={":new_status": "REFUNDED", ":new_type": "reversal"}  # Update TransactionType
            )
            print("Original transaction marked as REFUNDED with type 'reversal'.")
        except Exception as e:
            print(f"Error updating transaction status: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Error updating transaction status: {str(e)}"})
            }

        # Step 5: Mark audit entry as SUCCESS
        try:
            audit_table.update_item(
                Key={"AuditID": audit_id},
                UpdateExpression="SET #s = :new_status",
                ExpressionAttributeNames={"#s": "Status"},
                ExpressionAttributeValues={":new_status": "SUCCESS"}
            )
            print("Audit entry marked as SUCCESS.")
        except Exception as e:
            print(f"Error updating audit entry status: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Error updating audit entry status: {str(e)}"})
            }

        # Return success message
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Transaction reversed successfully"})
        }

    except Exception as e:
        # Handle unexpected errors
        print(f"Error occurred: {str(e)}")  # Log the actual exception
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"An internal server error occurred: {str(e)}"})
        }
