from HealthPipeline.app.silver_pipeline.transformations.flatten_metrics import flatten_bronze_to_silver

if __name__ == "__main__":
    input_path = "bronze_pipeline/outputData/parquetOut/"
    output_path = "silver_pipeline/outputData/flat_metrics/"
    flatten_bronze_to_silver(input_path, output_path)