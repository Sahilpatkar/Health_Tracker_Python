from pyspark.sql import SparkSession

# Create Spark Session
spark = SparkSession.builder \
    .appName("BigMart Analysis") \
    .getOrCreate()

# Example: Create a DataFrame
# data = [("James", "Sales", 3000),
#         ("Michael", "Sales", 4600),
#         ("Robert", "Sales", 4100),
#         ("Maria", "Finance", 3000)]

# columns = ["Employee Name", "Department", "Salary"]
#
# df = spark.createDataFrame(data, schema=columns)

# # Save it to output folder
# df.write.csv("Metrics/employee_data", header=True)
raw_df=spark.read.json(input.json)







print("Data written successfully.")

spark.stop()
