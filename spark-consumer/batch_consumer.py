"""
# batch_consumer.py
Bu modül, Spark kullanarak Kafka'dan gelen arama verilerini okur,
en çok arama yapılan şehir ve ürünleri analiz eder ve MongoDB'ye yazar.
"""
from pyspark.sql import SparkSession # type: ignore
from pyspark.sql.functions import col, from_json, desc # type: ignore
from pyspark.sql.types import StructType, StructField, StringType, LongType #type: ignore
import os
from utils.logger import setup_logger

logger = setup_logger("batch_consumer")  # Logger'ı ayarlıyoruz

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
    logger.info("Spark session oluşuturuldu.")
    
    kafka_topic = "search-logs"
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    logger.debug(f"Kafka'ya bağlanılıyor: {kafka_server}")

    kafka_df = ( spark.read
        .format("kafka") 
        .option("kafka.bootstrap.servers", kafka_server) 
        .option("subscribe", kafka_topic) 
        .option("startingOffsets", "earliest") # Topic'teki TÜM mesajları en baştan itibaren oku
        .load()
    )

    logger.info("Kafka'dan ham veri okundu. Ham verinin şeması:")
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
    logger.info("Veri kafkadan okundu ve ayrıştırıldı.")

    record_count = parsed_df.count()  # Toplam kayıt sayısını al
    logger.info(f"Toplam kayıt sayısı: {record_count}")

    if record_count > 0:
        logger.info("Ayrıştırılmış verinin ilk 10 kaydı:")
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
    logger.info("En çok arama yapılan 10 şehir:")
    top_10_cities.show(truncate=False)
    logger.info("En çok araması yapılan 10 ürün:")
    top_10_searches.show(truncate=False)
    
    
    logger.info("Veriler MongoDB'ye yazılıyor...")

    # Her bir yazma işlemini kendi try-except bloğuna almak,
    # biri başarısız olursa diğerinin denenmesine olanak tanır.
    try:
        logger.info(f"'top_10_sehirler' koleksiyonuna yazılıyor...")
        (
        top_10_cities.write.format("mongodb") 
                     .mode("overwrite") 
                     .option("collection", "top_10_sehirler") 
                     .save()
        )
        logger.info("'top_10_sehirler' koleksiyonuna başarıyla yazıldı.")
    except Exception as e:
        # Hata durumunda, hatayı loglayarak programın çökmesini engelliyoruz.
        logger.error(f"'top_10_sehirler' koleksiyonuna yazılırken bir hata oluştu: {e}")

    try:
        logger.info(f"'top_10_aramalar' koleksiyonuna yazılıyor...")
        (
        top_10_searches.write.format("mongodb") 
                       .mode("overwrite") 
                       .option("collection", "top_10_aramalar") 
                       .save()
        )
        logger.info("'top_10_aramalar' koleksiyonuna başarıyla yazıldı.")
    except Exception as e:
        logger.error(f"'top_10_aramalar' koleksiyonuna yazılırken bir hata oluştu: {e}")


    spark.stop()  # Spark oturumunu kapat
    logger.info("Spark oturumu kapatıldı.")

if __name__ == "__main__":
    main()  # Ana fonksiyonu çalıştır
# Bu kod, Kafka'dan veri okuma ve ayrıştırma işlemlerini gerçekleştirir. 
# Spark oturumu başlatılır, Kafka'dan veriler okunur, ayrıştırılır ve sonuçlar konsola yazdırılır. 
# Spark oturumu sonunda kapatılır. 
# Bu kodu çalıştırmadan önce Spark ve Kafka'nın doğru şekilde yapılandırıldığından emin olun. 
# Ayrıca, Kafka topic'inin adı ve bootstrap server adresi doğru şekilde ayarlanmalıdır. 