
import os
import json
import time
import boto3

sqs = boto3.client(
    "sqs",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

QUEUE_URL = os.getenv("SQS_QUEUE_URL")

if not QUEUE_URL:
    raise ValueError("SQS_QUEUE_URL environment variable is required")

print("E-commerce SQS worker started")

while True:

    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20,
        VisibilityTimeout=60
    )

    messages = response.get("Messages", [])

    for message in messages:

        try:
            order = json.loads(message["Body"])

            print("Processing order:", order)

            # Simulate order processing
            time.sleep(10)

            print("Order processed:", order["order_id"])

            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=message["ReceiptHandle"]
            )

        except Exception as error:
            print("Processing failed:", error)

    time.sleep(1)
