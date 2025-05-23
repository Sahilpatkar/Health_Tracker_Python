FROM openjdk:11-jre-slim

ENV SPARK_VERSION=3.2.0
ENV HADOOP_VERSION=3.2

RUN apt-get update && \
    apt-get install -y curl tar

RUN curl -fSL "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" -o /tmp/spark.tgz && \
    tar -xvf /tmp/spark.tgz -C /opt/ && \
    ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark && \
    rm /tmp/spark.tgz

RUN apt-get install -y python3 python3-pip
RUN pip3 install pyspark

RUN curl -fSL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.2.0/hadoop-aws-3.2.0.jar" -o /opt/spark/jars/hadoop-aws-3.2.0.jar
RUN curl -fSL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.534/aws-java-sdk-bundle-1.11.534.jar" -o /opt/spark/jars/aws-java-sdk-bundle-1.11.534.jar

COPY . /app

WORKDIR /app

ENTRYPOINT ["spark-submit",  "--packages", "org.apache.hadoop:hadoop-aws:3.2.0,com.amazonaws:aws-java-sdk-bundle:1.11.534","main.py"]
