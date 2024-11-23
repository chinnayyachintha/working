# Transaction and Audit Table Documentation

This repository provides a comprehensive schema and design for a **Transaction Table** and an **Audit Table** to track payment transactions and log associated actions. These tables are essential for maintaining transaction records, ensuring accountability, and enhancing security and compliance.

---

## **Transaction Table**

### **Purpose**
The **Transaction Table** is designed to store and manage details of various payment transactions, including sales, refunds, voids, and reversals. It helps track the lifecycle of each transaction and provides insights for customers, merchants, and system administrators.

### **Attributes**
| Attribute             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `transaction_id`      | Unique identifier for each transaction (Primary Key).                      |
| `parent_transaction_id` | Links to the original transaction for related transactions (e.g., refunds). |
| `customer_id`         | Identifier for the customer associated with the transaction.               |
| `merchant_id`         | Identifier for the merchant accepting the payment.                         |
| `amount`              | Total amount involved in the transaction.                                  |
| `currency`            | Currency code (e.g., USD, EUR, INR).                                       |
| `transaction_type`    | Type of transaction (SALE, REFUND, REVERSAL, VOID).                        |
| `source`              | Origin of the transaction (WEB, MOBILE_APP, POS).                         |
| `status`              | Status of the transaction (PENDING, SUCCESS, FAILED, CANCELLED).           |
| `timestamp`           | Timestamp when the transaction was created or updated.                    |
| `payment_method`      | Payment method used (CREDIT_CARD, DEBIT_CARD, WALLET, etc.).               |
| `processor_response`  | Response details from the payment processor, including error messages.     |
| `reference_id`        | External system reference ID.                                              |
| `authorization_code`  | Code for approved payments (if applicable).                               |
| `is_recurring`        | Boolean flag for recurring payments.                                       |
| `source_ip`           | IP address of the originating system for fraud detection.                 |
| `metadata`            | Key-value pairs for additional data (e.g., promo codes, affiliate info).   |

---

## **Audit Table**

### **Purpose**
The **Audit Table** provides a detailed log of actions performed on transactions, ensuring traceability, security, and transparency. It tracks access, updates, and changes to transaction data.

### **Attributes**
| Attribute             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `audit_id`            | Unique identifier for each audit log entry (Primary Key).                  |
| `transaction_id`      | Links to the associated transaction in the Transaction Table.              |
| `user_id`             | Identifier for the user or system performing the action.                  |
| `action`              | Type of action performed (CREATE, READ, UPDATE, DELETE).                  |
| `timestamp`           | Timestamp of when the action occurred.                                     |
| `source_ip`           | IP address of the system initiating the action.                           |
| `result`              | Outcome of the action (SUCCESS, FAILURE).                                 |
| `action_details`      | Description of the action, including old/new values for updates.          |
| `related_service`     | Service or system that initiated the action (FRONTEND, BACKEND, etc.).    |
| `metadata`            | Additional context for the action, stored as key-value pairs.             |

---
