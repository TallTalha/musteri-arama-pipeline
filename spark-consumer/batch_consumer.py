from pyspark.sql import SparkSession # type: ignore
from pyspark.sql.functions import col, from_json, desc # type: ignore
from pyspark.sql.types import StructType, StructField, StringType, LongType #type: ignore
import os

def main():

    kafka_mongo_connector_packages = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.3.0"
    mongo_con_uri = "mongodb://localhost:27017/eticaret.analizler"
    # SparkSession oluştur
    spark = ( SparkSession.builder
        .appName("KafkaToMongoBatchJob")  
        .master("local[*]") 
        .config("spark.jars.packages", kafka_mongo_connector_packages)
        .config("spark.mongodb.write.connection.uri",mongo_con_uri)
        .getOrCreate()
    ) 
    
    spark.sparkContext.setLogLevel("WARN")  # Log seviyesini WARN olarak ayarla
    print("Spark session oluşuturuldu.")
    
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
    parsed_df.cache()
    print("Veri kafkadan okundu ve ayrıştırıldı.")

    record_count = parsed_df.count()  # Toplam kayıt sayısını al
    print(f"Toplam kayıt sayısı: {record_count}")

    if record_count > 0:
        print("Ayrıştırılmış verinin ilk 10 kaydı:")
        parsed_df.show(10, truncate=False)

    # En Çok Arama Yapan 10 Şehir
    top_10_cities = ( parsed_df
        .groupBy("region")
        .count()
        .orderBy(col("count").desc())
        .limit(10)
    )

    # En çok Arama Yapılan 10 Ürün
    top_10_searches = ( parsed_df
        .groupBy("search")
        .count()
        .orderBy(col("count").desc())
        .limit(10)
    )

    # Lazy Evulation Tetikleyicisi
    # Spark show/write gibi bir aksiyon görene kadar işlemleri gerçekten çalıştırmaz.
    print("En çok arama yapılan 10 şehir:")
    top_10_cities.show(truncate=False)
    print("En çok araması yapılan 10 ürün:")
    top_10_searches.show(truncate=False)
    
    
    print("Veriler MongoDB'ye yazılıyor...")
    (
        top_10_cities.write
        .format("mongodb")
        .mode("overwrite")
        .option("collection","top_10_sehirler")
        .save()
    )
    (
        top_10_searches.write
        .format("mongodb")
        .mode("overwrite")
        .option("collection","top_10_aramalar")
        .save()
    )

    spark.stop()  # Spark oturumunu kapat
    print("Spark oturumu kapatıldı.")

if __name__ == "__main__":
    main()  # Ana fonksiyonu çalıştır
# Bu kod, Kafka'dan veri okuma ve ayrıştırma işlemlerini gerçekleştirir. 
# Spark oturumu başlatılır, Kafka'dan veriler okunur, ayrıştırılır ve sonuçlar konsola yazdırılır. 
# Spark oturumu sonunda kapatılır. 
# Bu kodu çalıştırmadan önce Spark ve Kafka'nın doğru şekilde yapılandırıldığından emin olun. 
# Ayrıca, Kafka topic'inin adı ve bootstrap server adresi doğru şekilde ayarlanmalıdır. 