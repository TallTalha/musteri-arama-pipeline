from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, LongType
import os

def main():
    # SparkSession oluştur
    spark = ( SparkSession.builder
        .appName("KafkaBatchConsumer")  
        .master("local[*]") 
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
        .getOrCreate()
    ) 
    
    spark.sparkContext.setLogLevel("WARN")  # Log seviyesini WARN olarak ayarla

    kafka_topic = "search-logs"
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    print(f"Kafka'ya bağlanılıyor: {kafka_server}")

    kafka_df = ( spark.read
        .format("kafka") 
        .option("kafka.bootstrap.servers", kafka_server) 
        .option("subscribe", kafka_topic) 
        .option("startingOffsets", "earliest") # Topic'teki TÜM mesajları en baştan itibaren oku
        .load()
    )

    print("Kafka'dan ham veri okundu. Ham verinin şeması:")
    kafka_df.printSchema() # Ham Kafka verisinin şemasını görelim

    # Kafka'dan veri okuma için uygun schema tanımlar
    schema = StructType([
        StructField("search", StringType(), True),
        StructField("timestamp", LongType(), True),
        StructField("region", StringType(), True)
    ])
    
    parsed_df = kafka_df.select(
    from_json(col("value").cast("string"), schema).alias("data")  # JSON string'i uygun schema ile ayrıştır
    ).select("data.*")  # Sadece ayrıştırılmış veriyi seç

    record_count = parsed_df.count()  # Toplam kayıt sayısını al
    print(f"Toplam kayıt sayısı: {record_count}")

    if record_count > 0:
        print("Ayrıştırılmış verinin ilk 10 kaydı:")
        parsed_df.show(10, truncate=False)

    spark.stop()  # Spark oturumunu kapat
    print("Spark oturumu kapatıldı.")

if __name__ == "__main__":
    main()  # Ana fonksiyonu çalıştır
# Bu kod, Kafka'dan veri okuma ve ayrıştırma işlemlerini gerçekleştirir. 
# Spark oturumu başlatılır, Kafka'dan veriler okunur, ayrıştırılır ve sonuçlar konsola yazdırılır. 
# Spark oturumu sonunda kapatılır. 
# Bu kodu çalıştırmadan önce Spark ve Kafka'nın doğru şekilde yapılandırıldığından emin olun. 
# Ayrıca, Kafka topic'inin adı ve bootstrap server adresi doğru şekilde ayarlanmalıdır. 