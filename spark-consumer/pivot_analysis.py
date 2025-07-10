from pyspark.sql import SparkSession # type: ignore
from pyspark.sql import DataFrame # type: ignore
from pyspark.sql.functions import col, from_json, desc, to_timestamp # type: ignore
from pyspark.sql.types import StructType, StructField, StringType, IntegerType #type: ignore
from kafka.errors import KafkaError 
import os

def main():
    kafka_mongo_connector_packages = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.mongodb.spark:mongo-spark-connector_2.12:10.3.0"
    mongo_con_uri = "mongodb://localhost:27017/eticaret"    

    spark = (
        SparkSession.builder
        .appName("PivotAnalysisJob")
        .master("local[*]")
        .config("spark.jars.packages", kafka_mongo_connector_packages)
        .config("spark.mongodb.write.connection.uri", mongo_con_uri)
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")  # Log seviyesini WARN olarak ayarla
    print("Spark session oluşturuldu.")

    kafka_topic = "search-analysis-userid"
    kafka_server = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        print(f"Kafka topiğine bağlanılıyor: {kafka_topic} sunucu: {kafka_server}")
        kafka_df = (
            spark.read
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_server)  # Kafka sunucusunu belirt
            .option("subscribe", kafka_topic)  # Kafka topic'ini belirt
            .option("startingOffsets", "earliest")  # Topic'teki tüm mesajları en baştan itibaren oku
            .load() 
        )
    except KafkaError as e:
        print(f"Kafka'ya topiğine bağlanırken hata oluştu: {e}")
        return 0

    schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("search", StringType(), True),
        StructField("region", StringType(), True),
        StructField("timestamp", StringType(), True)
    ])

    parsed_df = kafka_df.select(
        from_json(
            col("value").cast("string"), schema
        ).alias("data")  # JSON string'i uygun schema ile ayrıştır
    ).select("data.*")  # Sadece ayrıştırılmış veriyi seç

    # Zaman Damgasını Doğru Tipe Çevirme
    # `withColumn` ile 'timestamp' sütununu, `to_timestamp` fonksiyonu kullanarak
    # metinden gerçek bir zaman damgası tipine dönüştürüyoruz.
    final_df = parsed_df.withColumn("timestamp", to_timestamp(col("timestamp")))
    final_df.printSchema()  # Şemayı kontrol et

    print("Veri Kafka'dan okundu ve ayrıştırıldı.")

    final_df.cache()  # Veriyi önbelleğe al
    record_count = final_df.count()  # Toplam kayıt sayısını al
    print(f"Toplam kayıt sayısı: {record_count}")

    # Pivot Analizi: Kullanıcı ID'lerine Göre Arama Terimleri
    search_by_userid_df = (
        final_df.groupBy("user_id", "search")
        .count()
    )
    pivot_df = (
        search_by_userid_df.groupBy("user_id")
        .pivot("search")
        .sum("count")  # Her kullanıcı için arama terimlerinin toplam sayısını al
    ).na().fill(0)  # NaN değerleri 0 ile doldur

    print("Pivot analizi tamamlandı. İlk 10 kayıt:")
    pivot_df.show(10, truncate=False)  # İlk 10 kaydı göster

    # Sonucu MongoDB'ye yazma
    try:
        (
        pivot_df.write 
            .format("mongodb") 
            .mode("overwrite") 
            .option("collection", "search_by_userid_pivot") 
            .save()
        )
        print("Pivot analizi MongoDB'ye başarıyla yazıldı.")
    except Exception as e:
        print(f"MongoDB'ye yazılırken hata oluştu: {e}")
    
    spark.stop()  # Spark oturumunu kapat

if __name__ == "__main__":
    main()