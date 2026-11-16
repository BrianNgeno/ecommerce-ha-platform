
import os
import json
import uuid
import boto3
import redis

from flask import Flask, jsonify, request

app = Flask(__name__)

# AWS configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION
)

# Redis configuration
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
    socket_connect_timeout=2
)


@app.route("/")
def home():
    return jsonify({
        "message": "E-commerce application running successfully",
        "status": "healthy"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/products")
def products():

    try:
        cached_products = redis_client.get("products")

        if cached_products:
            return jsonify({
                "source": "Redis cache",
                "products": json.loads(cached_products)
            })

        product_data = [
            {"id": 1, "name": "Laptop", "price": 85000},
            {"id": 2, "name": "Phone", "price": 45000},
            {"id": 3, "name": "Headphones", "price": 5000}
        ]

        redis_client.setex(
            "products",
            300,
            json.dumps(product_data)
        )

        return jsonify({
            "source": "Application database",
            "products": product_data
        })

    except redis.RedisError:
        # Continue operating if the cache is unavailable
        return jsonify({
            "source": "Fallback",
            "products": [
                {"id": 1, "name": "Laptop", "price": 85000},
                {"id": 2, "name": "Phone", "price": 45000},
                {"id": 3, "name": "Headphones", "price": 5000}
            ]
        })


@app.route("/orders", methods=["POST"])
def create_order():

    if not QUEUE_URL:
        return jsonify({"error": "SQS queue not configured"}), 503

    order = request.get_json(silent=True)

    if not order:
        return jsonify({"error": "Invalid order data"}), 400

    order_id = str(uuid.uuid4())

    message = {
        "order_id": order_id,
        "customer": order.get("customer"),
        "product": order.get("product"),
        "quantity": order.get("quantity", 1)
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message)
    )

    return jsonify({
        "message": "Order submitted successfully",
        "order_id": order_id,
        "sqs_message_id": response["MessageId"]
    }), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
