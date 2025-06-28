import boto3
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import io
import dlt

from dlt.common import pendulum


#s3://sc-sibel-destination-distro/sibel_shrd_decoded/package_version=0.8.2/

def main():


    # Setup S3
    s3 = boto3.client("s3")
    bucket_name = "sc-sibel-destination-distro"
    prefix = "sibel_shrd_decoded/package_version=0.8.2/"  # Folder where your Parquet files are stored
    threshold_bytes = 100 * 1024 * 1024  # 100 MB

    # List .parquet files
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".parquet")]

    def parquet_generator():
        for file_key in files:
            print(f"\n▶ Processing file: {file_key}")

            # Get file size
            metadata = s3.head_object(Bucket=bucket_name, Key=file_key)
            size = metadata["ContentLength"]
            print(f"Size: {size / (1024 * 1024):.2f} MB")

            # Fetch file from S3
            response = s3.get_object(Bucket=bucket_name, Key=file_key)
            stream = io.BytesIO(response["Body"].read())

            if size <= threshold_bytes:
                # Small file: load all at once
                df = pd.read_parquet(stream)
                for row in df.to_dict(orient="records"):
                    yield row
            else:
                # Large file: read in batches
                parquet_file = pq.ParquetFile(stream)
                for batch in parquet_file.iter_batches(batch_size=5000):
                    table = pa.Table.from_batches([batch])
                    df_chunk = table.to_pandas()
                    for row in df_chunk.to_dict(orient="records"):
                        yield row


    # Create the pipeline
    pipeline = dlt.pipeline(
        pipeline_name="parquet_to_iceberg",
        destination="iceberg_lake",
        dataset_name="SibelPatchTest"
    )

    # Configure Iceberg destination settings
    iceberg_config = {
        'database': 'default_db',
        'warehouse_path': 's3://sensorcloud-lakehouse-distro/iceberg_catalog',
        "catalog": "glue",
        'region': 'your-aws-region',
        'table_name': 'sibel_patch_data'
    }

    # Initialize the pipeline with the configuration
    load_info = pipeline.run(
        data=parquet_generator(),
        destination_name="iceberg",  # Specify the destination name
        table_name="sibel_patch_data",  # Specify the table name here as well
        write_disposition="replace",  # Options: append, replace, merge
        destination=iceberg_config
    )

    # # Now set destination configuration via config
    # pipeline.config["destination.iceberg"] = {
    #     "warehouse": "s3://sensorcloud-lakehouse-distro/iceberg_catalog",  # Your Iceberg warehouse
    #     "catalog": "glue",
    #     "catalog_name": "default_db",
    #     "aws_region": "us-east-1"
    # }

    # Run the pipeline with your generator
    #load_info = pipeline.run(parquet_generator(), table_name="sensor_data")

    print("\n✅ Load completed.")
    print(load_info)






if __name__ == "__main__":
     main()


