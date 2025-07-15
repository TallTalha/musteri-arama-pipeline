"""
trending_topic_analysis.py
Bu modül, Spark kullanarak Kafka'dan gelen arama verilerini okur,
günün 30 dakikalık dilimlerinde en çok arama yapılan ürünleri analiz eder
ve MongoDB'ye yazar.
"""
from pyspark.sql import SparkSession  # type: ignore
from pyspark.sql.functions import col, from_json, desc, window  # type: ignore
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType  # type: ignore
from kafka.errors import KafkaError
import os
from utils.logger import setup_logger

logger = setup_logger("trending_topic_analysis")  

def main():
    logger.info("Trending Topic Analysis Job başlatılıyor...")
    packages = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.3.0"
    mongo_con_uri = "mongodb://localhost:27017/eticaret"
    # Spark Session oluştur
    logger.info("Spark Session oluşturuluyor...")
    spark = (
        SparkSession.builder
        .appName("TrendingTopicAnalysisJob")
        .master("local[*]")
        .config("spark.jars.packages", packages)
        .config("spark.mongodb.write.connection.uri", mongo_con_uri)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")  # Log seviyesini WARN olarak ayarla
    logger.info("Spark session oluşturuldu.")

    # Kafka'dan veri okuma
    kafka_topic = "search-analysis-userid"
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        logger.info(f"kafka topiğine bağlanılıyor: {kafka_topic} sunucu: {kafka_server}")
        kafka_df = (
            spark.read
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_server)
            .option("subscribe", kafka_topic)
            .option("startingOffsets", "earliest")  # Topic'teki tüm mesajları en baştan itibaren oku
            .load()
        )
        logger.info("Kafka'dan veri okundu.")
    except KafkaError as e:
        logger.error(f"Kafka'ya bağlanırken hata oluştu: {e}")
        return 0
    
    # Kafka'dan okunan veri için anlamlı bir şema tanımla
    schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("search", StringType(), True),
        StructField("region", StringType(), True),
        StructField("timestamp", StringType(), True)
    ])

    # JSON string'i uygun schema ile ayrıştırır
    parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")  # Sadece ayrıştırılmış veriyi seç

    # Zaman Damgasını Doğru Tipe Çevirme
    parsed_df = parsed_df.withColumn("timestamp_dt", col("timestamp").cast(TimestampType()))
    logger.info("Veri ayrıştırıldı ve zaman damgası tipi düzeltildi.")

    # 30 dakikalık zaman dilimlerinde en çok arama yapılan ürünleri bul
    trending_df = (
        parsed_df
        .groupBy(
            window(col("timestamp_dt"), "30 minutes"),  # 30 dakikalık zaman dilimleri
            col("search")  # Arama terimi
        )
        .count()  # Her grup için sayım yap
        .orderBy(desc("count"))  # En çok arama yapılanları sırala
    )


    # MongoDB'ye yazma işlemi için DataFrame'i uygun formata dönüştür
    trending_df = (
        trending_df.select(
            col("window.start").alias("start_time"),
            col("window.end").alias("end_time"),
            col("search"),
            col("count")
        )
    )

    logger.info("Gün içinde, 30 dakikalık dilimlerde yapılan aramalar hesaplandı.Özet sonuçlar:")
    trending_df.show(10, truncate=False)  
    
    # MongoDB'ye yazma işlemi
    try:
        logger.info("MongoDB'ye yazma işlemi başlatılıyor...")
        (
            trending_df.write
            .format("mongodb")
            .mode("overwrite")  # Eski verileri sil ve yeni verileri yaz
            .option("collection", "trending_searches_30min")  # MongoDB koleksiyonu
            .save()  # Veriyi MongoDB'ye kaydet
        ) 
    except Exception as e:
        logger.error(f"MongoDB'ye yazma işlemi sırasında hata oluştu: {e}")
        return 0
    logger.info("MongoDB'ye yazma işlemi başarılı.")
    spark.stop()  # Spark oturumunu kapat
    logger.info("Spark oturumu kapatıldı.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Uygulama çalışırken hata oluştu: {e}", exc_info=True)
    finally:
        logger.info("Uygulama oturumu sonlandırıldı.")  


        