import boto3
import os
from botocore.exceptions import ClientError
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Retrieve environment variables
DYNAMODB_LEDGER_TABLE_NAME = os.getenv('DYNAMODB_LEDGER_TABLE_NAME')
DYNAMODB_AUDIT_TABLE_NAME = os.getenv('DYNAMODB_AUDIT_TABLE_NAME')
KMS_KEY_ARN = os.getenv('KMS_KEY_ARN')

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')
kms_client = boto3.client('kms')

# Connect to DynamoDB tables
payment_ledger_table = dynamodb.Table(DYNAMODB_LEDGER_TABLE_NAME)
audit_table = dynamodb.Table(DYNAMODB_AUDIT_TABLE_NAME)

# Helper Function: Encrypt SecureToken using KMS
def encrypt_token(token):
    try:
        response = kms_client.encrypt(
            KeyId=KMS_KEY_ARN,
            Plaintext=token.encode('utf-8')
        )
        return response['CiphertextBlob']
    except ClientError as e:
        logger.error(f"Error encrypting token: {e.response['Error']['Message']}")
        raise Exception(f"Error encrypting token: {e.response['Error']['Message']}")

# Step 1: Persist Payment Ledger Entry
def persist_payment_ledger(amount, processor_id, source, transaction_type):
    transaction_id = str(uuid.uuid4())
    status = "Initiated"
    try:
        payment_ledger_table.put_item(
            Item={
                'TransactionID': transaction_id,
                'Amount': amount,
                'ProcessorID': processor_id,
                'Status': status,
                'Source': source,  # Include source in the ledger entry
                'TransactionType': transaction_type,  # Include transaction type
                'Timestamp': str(datetime.now(timezone.utc))  # Ensure time zone aware
            }
        )
        logger.info(f"Payment ledger entry created for transaction {transaction_id} from source {source} with type {transaction_type}")
        return transaction_id
    except ClientError as e:
        logger.error(f"Error storing payment initiation: {e.response['Error']['Message']}")
        raise Exception(f"Error storing payment initiation: {e.response['Error']['Message']}")

# Step 2: Process Payment Response with Transaction Type Logic
def process_payment_response(transaction_id, amount, processor_id, processor_response, source, transaction_type):
    normalized_status = normalize_processor_response(processor_response)
    query_details = f"Payment processed for amount: {amount} using processor: {processor_id} from source: {source} with type {transaction_type}"
    response_data = f"Processor response: {processor_response}"

    try:
        # Handle different transaction types
        if transaction_type == 'SALE':
            if normalized_status == 'success':
                update_payment_status(transaction_id, "Success")
            elif normalized_status == 'failed':
                update_payment_status(transaction_id, "Failed")
            elif normalized_status == 'pending':
                update_payment_status(transaction_id, "Pending")
            
            persist_payment_audit_trail(transaction_id, query_details, response_data, source)

        elif transaction_type == 'REFUND':
            if normalized_status == 'success':
                update_payment_status(transaction_id, "Refunded")
            elif normalized_status == 'failed':
                update_payment_status(transaction_id, "Refund Failed")
            elif normalized_status == 'pending':
                update_payment_status(transaction_id, "Refund Pending")
            
            persist_payment_audit_trail(transaction_id, query_details, response_data, source)

        elif transaction_type == 'VOID':
            update_payment_status(transaction_id, "Voided")
            persist_payment_audit_trail(transaction_id, query_details, response_data, source)

        elif transaction_type == 'REVERSAL':
            update_payment_status(transaction_id, "Reversed")
            persist_payment_audit_trail(transaction_id, query_details, response_data, source)

        else:
            logger.error(f"Invalid transaction type: {transaction_type}")
            return {
                'statusCode': 400,
                'body': f"Invalid transaction type: {transaction_type}"
            }

        return {
            'statusCode': 200,
            'body': f"Transaction {transaction_type} processed for transaction {transaction_id}"
        }

    except Exception as e:
        logger.error(f"Error processing payment response: {str(e)}")
        raise Exception(f"Error processing payment response: {str(e)}")

# Step 3: Update Payment Status
def update_payment_status(transaction_id, status):
    try:
        payment_ledger_table.update_item(
            Key={'TransactionID': transaction_id},
            UpdateExpression="set #status = :status",
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': status},
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Payment status updated for transaction {transaction_id} to {status}")
    except ClientError as e:
        logger.error(f"Error updating payment status: {e.response['Error']['Message']}")
        raise Exception(f"Error updating payment status: {e.response['Error']['Message']}")

# Step 4: Persist Audit Trail
def persist_payment_audit_trail(transaction_id, query_details, response_data, source):
    try:
        audit_id = str(uuid.uuid4())
        audit_table.put_item(
            Item={
                'AuditID': audit_id,
                'TransactionID': transaction_id,
                'QueryDetails': query_details,
                'ResponseData': response_data,
                'Source': source,  # Include source in the audit trail
                'Timestamp': str(datetime.now(timezone.utc))  # Time zone aware
            }
        )
        logger.info(f"Audit trail created for transaction {transaction_id} from source {source}")
    except ClientError as e:
        logger.error(f"Error creating audit trail: {e.response['Error']['Message']}")
        raise Exception(f"Error creating audit trail: {e.response['Error']['Message']}")

# Lambda Handler Function
def lambda_handler(event, context):
    try:
        # Extract and validate input
        amount = Decimal(str(event['amount']))
        processor_id = event['processor_id']
        source = event.get('source', 'unknown')  # Capture source from event, default to 'unknown'
        transaction_type = event.get('transaction_type', 'SALE')  # Get transaction type from event
        simulate_status = event.get('simulate_status', '').lower()

        # Step 1: Persist the payment ledger entry
        transaction_id = persist_payment_ledger(amount, processor_id, source, transaction_type)

        # Step 2: Create a secure token
        encrypted_token = create_secure_token(amount, processor_id)

        # Step 3: Simulate the processor response
        processor_response = {
            'status': simulate_status,
            'transaction_id': transaction_id,
            'amount': amount,
            'processor_id': processor_id
        }

        # Step 4: Process the simulated payment response based on the transaction type
        return process_payment_response(transaction_id, amount, processor_id, processor_response, source, transaction_type)

    except Exception as e:
        logger.error(f"Error in payment processing flow: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error in payment processing flow: {str(e)}"
        }
