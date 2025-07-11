from pyspark.sql import SparkSession # type: ignore
from pyspark.sql.functions import col, from_json, desc, to_timestamp # type: ignore
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType #type: ignore
from kafka.errors import KafkaError
import os
from utils.logger import setup_logger   

logger = setup_logger("streaming_consumer")  # Logger'ı başlat

def main():
    # SPARK SESSION
    logger.info("Spark Session oluşturuluyor...")
    packages = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"
    spark = (
        SparkSession.builder
        .appName("KafkaRealtimeConsumer")
        .master("local[*]")
        .config("spark.jars.packages", packages)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")  # Log seviyesini WARN olarak ayarla
    logger.info("Spark session oluşturuldu.")

    #EXTRACT KAFKA DATA
    kafka_topic = "search-analysis-stream"
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    logger.info(f"'{kafka_topic}' topic'i dinlenmeye başlanıyor...")
    kafka_df =(
        spark.readStream
        .format("kafka")  # Kafka'dan veri okuyacağımızı belirtiyoruz
        .option("kafka.bootstrap.servers", kafka_server)  # Kafka sunucusunu belirt
        .option("subscribe", kafka_topic)  # Hangi topic'ten veri okuyacağımızı belirt
        .load()
    )

    # TRANSFORM KAFKA DATA
    schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("search", StringType(), True),
        StructField("region", StringType(), True),
        StructField("timestamp", StringType(), True)
    ])

    # JSON string'i uygun schema ile ayrıştır
    parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), schema) 
        .alias("data")  
    ).select("data.*")  # Sadece ayrıştırılmış veriyi seç
    
    # Zaman Damgasını Doğru Tipe Çevirme
    # `withColumn` ile 'timestamp' sütununu, `to_timestamp` fonksiyonu kullanarak
    # metinden gerçek bir zaman damgası tipine dönüştürüyoruz.
    final_df = parsed_df.withColumn("timestamp_dt", col("timestamp").cast(TimestampType()))

    # Konsolda verilerin akışı kontrol edilir
    logger.info("Streaming sorgusu başlatıldı ve konsola yazılıyor...")
    query = (
        final_df.writeStream
        .format("console")  # Konsola yazdırma formatı
        .outputMode("append")  # Sadece yeni eklenen verileri göster
        .option("truncate", "false")  # Uzun verileri kesme
        .start()  # Akışı başlat
    )

    # Streming sorgusunun sürekli olarak çalışmasını sağla
    query.awaitTermination()
    # Kulllanıcı akışı durdurmak isterse, Ctrl+C ile durdurabilir / Terminali kapatabilir.

if __name__ == "__main__":
    try:
        logger.info("Streaming consumer uygulaması başlatılıyor.")
        main() 

    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından uygulama sonlandırıldı (Ctrl+C).")
            
    except Exception as e:
        logger.critical(f"Uygulama kritik bir hatayla karşılaştı ve durduruluyor: {e}", exc_info=True)
            
    finally:
        logger.info("Uygulama oturumu sonlandı.")