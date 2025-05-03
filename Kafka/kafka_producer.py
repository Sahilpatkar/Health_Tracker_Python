import json
import os

from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()



def send_to_kafka(extracted_data):
    if not isinstance(extracted_data, dict):
        raise ValueError(f"Kafka payload must be a dict, got {type(extracted_data)}")

    try:
        producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVER"),
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        future = producer.send("health-report-data", value=extracted_data)
        result = future.get(timeout=10)
        print("Kafka send result:", result)
        producer.flush()
    except Exception as e:
        print(f"Failed to send to Kafka: {e}")
        raise

