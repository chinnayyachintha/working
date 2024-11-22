import boto3
import logging
import time
import json
import os

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')
sqs = boto3.client('sqs')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

TRANSACTIONS_TABLE = os.environ.get("TRANSACTIONS_TABLE")  # DynamoDB Table name for transactions
AUDIT_TRAIL_TABLE = os.environ.get("AUDIT_TRAIL_TABLE")  # DynamoDB Table for audit trail
FIFO_QUEUE_URL = os.environ.get("FIFO_QUEUE_URL")  # SQS FIFO Queue URL

def get_transaction(transaction_id):
    """Retrieve transaction details from DynamoDB."""
    try:
        response = dynamodb.get_item(
            TableName=TRANSACTIONS_TABLE,
            Key={'TransactionID': {'S': transaction_id}}  # Ensure key matches table schema
        )
        if 'Item' not in response:
            logger.error(f"Transaction {transaction_id} not found.")
            return None
        return response['Item']
    except Exception as e:
        logger.error(f"Error fetching transaction {transaction_id}: {e}")
        raise

def validate_transaction(transaction, transaction_type):
    """Validate if the transaction is eligible for specific actions."""
    status = transaction.get('Status', {}).get('S', '')
    
    # Validate based on the transaction type
    if transaction_type == 'VOID' and status != 'Completed':
        raise Exception(f"Transaction cannot be voided. Current status: {status}")
    elif transaction_type == 'REFUND' and status != 'Completed':
        raise Exception(f"Refund cannot be processed. Current status: {status}")
    # You can add more validations based on transaction type (e.g., for SALE)

def create_void_transaction(original_transaction, void_amount, reason):
    """Create a void transaction in DynamoDB."""
    void_transaction = {
        'TransactionID': {'S': f"{original_transaction['TransactionID']['S']}-VOID"},
        'TransactionType': {'S': 'VOID'},  # Set the transaction type as VOID
        'Status': {'S': 'Voided'},
        'OriginalTransactionID': {'S': original_transaction['TransactionID']['S']},
        'Amount': {'N': str(-float(void_amount))},
        'Reason': {'S': reason},
        'Timestamp': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ')},  # Keep Timestamp in void transaction
    }
    
    try:
        dynamodb.put_item(TableName=TRANSACTIONS_TABLE, Item=void_transaction)
        logger.info(f"Void transaction created: {void_transaction}")
        return void_transaction
    except Exception as e:
        logger.error(f"Error creating void transaction: {e}")
        raise

def log_audit_trail(original_transaction, void_transaction, user_id, reason):
    """Log the void action in the audit trail."""
    audit_entry = {
        'AuditID': {'S': f"{void_transaction['TransactionID']['S']}-AUDIT"},
        'OriginalTransactionID': {'S': original_transaction['TransactionID']['S']},
        'VoidTransactionID': {'S': void_transaction['TransactionID']['S']},
        'Amount': {'N': void_transaction['Amount']['N']},
        'Reason': {'S': reason},
        'User': {'S': user_id},
        'Timestamp': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ')}
    }
    try:
        dynamodb.put_item(TableName=AUDIT_TRAIL_TABLE, Item=audit_entry)
        logger.info(f"Audit trail logged: {audit_entry}")
    except Exception as e:
        logger.error(f"Error logging audit trail: {e}")
        raise

def send_to_fifo_queue(void_transaction):
    """Send void transaction details to SQS FIFO queue."""
    message = {
        'TransactionID': void_transaction['TransactionID']['S'],
        'Amount': void_transaction['Amount']['N'],
        'Reason': void_transaction['Reason']['S']
    }
    
    try:
        sqs.send_message(
            QueueUrl=FIFO_QUEUE_URL,
            MessageBody=json.dumps(message),
            MessageGroupId="void-transaction-group",
            MessageDeduplicationId=void_transaction['TransactionID']['S']
        )
        logger.info(f"Void transaction sent to FIFO queue: {message}")
    except Exception as e:
        logger.error(f"Error sending to FIFO queue: {e}")
        raise

def lambda_handler(event, context):
    """Lambda entry point to process void requests."""
    try:
        logger.info(f"Event received: {json.dumps(event)}")
        transaction_id = event.get('transactionId')
        user_id = event.get('userId')
        reason = event.get('reason')
        void_amount = event.get('voidAmount', 100.0)
        transaction_type = event.get('transactionType', 'VOID')  # Add transaction type from event

        if not all([transaction_id, user_id, reason]):
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields"})}

        transaction = get_transaction(transaction_id)
        if not transaction:
            return {"statusCode": 404, "body": json.dumps({"error": "Transaction not found"})}

        # Validate based on transaction type
        validate_transaction(transaction, transaction_type)

        # Handle void transaction if the type is VOID
        if transaction_type == 'VOID':
            void_transaction = create_void_transaction(transaction, void_amount, reason)
            log_audit_trail(transaction, void_transaction, user_id, reason)
            send_to_fifo_queue(void_transaction)
            return {"statusCode": 200, "body": json.dumps({"message": "Void processed successfully"})}
        
        # Optionally, you can handle REFUND or other types here.
        if transaction_type == 'REFUND':
            # Implement Refund logic here
            pass

        return {"statusCode": 400, "body": json.dumps({"error": "Unsupported transaction type"})}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
