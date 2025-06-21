import json

from confluent_kafka.avro import AvroProducer
from confluent_kafka import avro
import os
import logging

# Load env variables
from dotenv import load_dotenv
load_dotenv()

# Load Avro schema from file
base_dir = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(base_dir, "SerDe", "health_report.avsc")
value_schema = avro.load(schema_path)

# Initialize producer
producer = AvroProducer(
    {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVER_DOCKER"),
        'schema.registry.url': os.getenv("SCHEMA_REGISTRY_URL_DOCKER"),
        'acks': '1'
    },
    default_value_schema=value_schema
)
def stringify_values(data: dict) -> dict:
    if "params" in data:
        for param in data["params"].values():
            param["value"] = str(param["value"])  # force to string
    return data


def send_to_kafka_avro(extracted_data,topic):
    if not isinstance(extracted_data, dict):
        raise ValueError("extracted_data must be a dict")

    try:
        cleaned_data = stringify_values(extracted_data)
        producer.produce(topic=topic, value=cleaned_data)
        producer.flush()
        logging.info("Successfully sent data to Kafka with Avro serialization.")
    except Exception as e:
        logging.error(f"Error sending Avro message to Kafka: {e}")
        raise


if __name__ == "__main__":
    file_path = "../HealthReport/shashank/processed_report/2024-08-25T12:01:00/report_shashank_2024-08-25T12:01:00.json"
    json_data = json.load(open(file_path))
    send_to_kafka_avro(json_data,"health-report-data")