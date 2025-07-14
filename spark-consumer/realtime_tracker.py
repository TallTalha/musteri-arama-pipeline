import os
from pyspark.sql import SparkSession, DataFrame # type: ignore
from pyspark.sql.functions import col, from_json, lower # type: ignore
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType # type: ignore
from utils.logger import setup_logger

logger = setup_logger("realtime_tracker") 

def write_to_mongo(df: DataFrame, epoch_id: int, collection: str = "realtime_maske_searches") -> None:
    """
    Bu fonksiyon, DataFrame'i MongoDB'ye yazmak için kullanılır.
        Args:
            df (DataFrame): Yazılacak DataFrame.
            epoch_id (int): Epoch ID'si, genellikle işlem sırasını belirtir.
            collection (str): MongoDB koleksiyon adı, varsayılan olarak "realtime_maske_searches" kullanılır.
        Returns:
            None    
    """
    logger.info(f"Yazma işlemi başlatıldı, epoch_id: {epoch_id}")

    if df.count() == 0:
        logger.info("DataFrame boş, MongoDB'ye yazma işlemi atlandı.")
        return 
    
    logger.info(f" `maske´ ürününü içeren {df.count()} adette veri {collection} koleksiyonuna yazılacak.")
    (
        df.write
        .format("mongodb")
        .mode("append")
        .option("collection", collection)
        .save()
    )

    logger.info(f"epoch_id: {epoch_id}, {collection} koleksiyonuna yazma işlemi tamamlandı.")
    
def main():
    """
    Ana fonksiyon, Spark Session'ı başlatır ve 
    `maske´ içerikli verileri MongoDB'ye yazmak için gerekli işlemleri yapar.
        Args:
            None
        Returns:
            None
    """
    # Gerekli paketleri ve MongoDB bağlantı ayarları
    packages = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1"
    mongodb_uri = "mongodb://localhost:27017/eticaret"
    #Spark Session başlatma
    spark = (
        SparkSession.builder
        .appName("RealtimeMaskTracker")
        .master("local[*]")
        .config("spark.jars.packages", packages)
        .config("spark.mongodb.connection.uri", mongodb_uri)
        .getOrCreate()
    )
    logger.sparkContext.setLogLevel("WARN")
    logger.info("Spark Session başlatıldı.")

    # Kafka'dan veri okuma
    kafka_topic = "search-analysis-stream"
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_server)
        .option("subscribe", kafka_topic )
        .load()
    )

    # Schema tanımlama
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

    # `maske´ ürününü içeren verileri filtrelenir
    maske_df = parsed_df.filter(lower(col("search")).contains("maske"))

    # Zaman Damgasını Doğru Tipe Çevir
    maske_df = maske_df.withColumn("timestamp_dt", col("timestamp").cast(TimestampType()))

    # Anlık olarak işlenmiş veriler 10 saniyede bir MongoDB'ye yazılır
    query = (
        maske_df.writeStream
        .foreachBatch(write_to_mongo)  # Her batch için MongoDB'ye yazma işlemi
        .outputmode("append")  # Sadece yeni eklenen verileri göster
        .option("truncate", "false")  # Uzun verileri kesme
        .option("checkpointLocation", "checkpoint/realtime_tracker_v1")  # Checkpoint konumu
        .trigger(processingTime="10 seconds")  # Her 10 saniyede bir işlem yap
        .start()  # Akışı başlat
    )

    logger.info("Streaming sorgusu başlatıldı. Yeni veriler MongoDB'ye yazılıyor...")
    query.awaitTermination()  # Sorgunun sonlanmasını bekle

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Uygulama kritik bir hatayla karşılaştı: {e}", exc_info=True)
    finally:
        logger.info("Uygulama sonlandırılıyor.")




