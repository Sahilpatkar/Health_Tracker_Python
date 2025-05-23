#💥 Core transformation logic (Bronze → Silver)
from pyspark.sql import SparkSession


def flatten_bronze_to_silver(input_path: str,output_path: str):
    spark = (SparkSession.builder \
        .appName("HealthPipeline Bronze Layer") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .master("local[*]")
        .getOrCreate())

    # Step 1: Read from Bronze
    df= spark.read.parquet("../bronze_pipeline/outputData/parquetOut/*")

    # Step 2: Extract field names from the "Data" struct
    data_fields = df.select("Data.*").columns

