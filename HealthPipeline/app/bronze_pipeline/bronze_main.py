# 1. Import necessary libraries
# 2. Parse input and output paths from sys.argv
# 3. Create Spark session
# 4. Read input JSON
# 5. Validate: Show basic schema and row count
# 6. Write output as Parquet/CSV
# 7. Stop Spark
import sys

from pyspark.shell import spark
from pyspark.sql import SparkSession
from bronze_pipeline.schema.health_report_schema import health_report_schema

def main(input_path:str,output_path:str):
    # Step 1: Create SparkSession
    spark = (SparkSession.builder \
        .appName("HealthPipeline Bronze Layer") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .master("local[*]")
        .getOrCreate())


    try:
        # Step 4: Read input JSON
        df = spark.read.schema(health_report_schema).option("multiline","true").json(input_path)
        print("✅ Successfully read the input JSON file.")
        df.show(5);


    except Exception as e:
        print(f"❌ Error reading input JSON: {e}")
        spark.stop()
        return

    # Step 5: Write output to Parquet
    try:
        df.write.mode("overwrite").parquet(output_path)
        print(f"✅ Successfully wrote data to Parquet at: {output_path}")
    except Exception as e:
        print(f"❌ Error writing output data: {e}")

    # Step 5: Validate: Show basic schema and row count
    df.printSchema()
    print(f"Row count: {df.count()}")

        # # Step 6: Write output as Parquet/CSV
        # df.write.parquet("app/bronze_pipeline/outputData/csvOut/output.parquet", mode="overwrite")
        # df.write.csv("app/bronze_pipeline/outputData/parquetOut/output.csv", mode="overwrite", header=True)

        #print("Data processing completed successfully.")
 # Step 2: Stop SparkSession
spark.stop()

if __name__ == "__main__":
    # if len(sys.argv) != 3:
    #     print("Usage: bronze_main.py <input_path> <output_path>")
    #     sys.exit(1)
    #
    # input_path = sys.argv[1]
    # output_path = sys.argv[2]

    #input_path = sys.argv[1]
    input_path = "inputData/input2.json"
   # output_path = sys.argv[2]
    output_path = "outputData/parquetOut/"
    main(input_path,output_path)
