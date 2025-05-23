FROM openjdk:11-jre-slim

ENV SPARK_VERSION=3.2.0
ENV HADOOP_VERSION=3.2

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl tar python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Spark
RUN curl -fSL "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" -o /tmp/spark.tgz && \
    tar -xvf /tmp/spark.tgz -C /opt/ && \
    ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark && \
    rm /tmp/spark.tgz

# Install PySpark
RUN pip3 install pyspark

# Add S3 support
#RUN curl -fSL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.2.0/hadoop-aws-3.2.0.jar" -o /opt/spark/jars/hadoop-aws-3.2.0.jar && \
#    curl -fSL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.534/aws-java-sdk-bundle-1.11.534.jar" -o /opt/spark/jars/aws-java-sdk-bundle-1.11.534.jar

COPY . /app
WORKDIR /app

# Install Python requirements
RUN pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT ["spark-submit", "--packages", "org.apache.hadoop:hadoop-aws:3.2.0,com.amazonaws:aws-java-sdk-bundle:1.11.534", "app/main.py"]
