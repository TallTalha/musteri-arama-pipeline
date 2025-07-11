# 1. Gerekli kütüphaneleri import ediyoruz
from datetime import datetime
from fastapi import FastAPI #type: ignore
from kafka import KafkaProducer #  Kafka Producer'ı import ediyoruz
from kafka.errors import KafkaError #  Olası Kafka hatalarını yakalamak için
import time
import random
import json
from utils.logger import setup_logger

logger = setup_logger("api_main")  # Logger'ı ayarlıyoruz

# 2. Kafka Producer'ı yapılandır ve oluştur (Uygulama Seviyesinde)
try:
    producer = KafkaProducer(
        # Kafka broker'ımızın adresini belirtiyoruz. Tünel sayesinde localhost kullanıyoruz.
        bootstrap_servers="localhost:9092",
        
        # Kafka'ya göndereceğimiz değerleri (value) nasıl serialize edeceğimizi belirtiyoruz.
        # Bizim değerimiz bir Python dictionary (JSON objesi). Onu önce JSON string'e,
        # sonra da Kafka'nın anladığı byte formatına (`utf-8`) çeviriyoruz.
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    logger.info("Kafka Producer bağlantısı başarıyla kuruldu.")
except KafkaError as e:
    # Eğer Kafka çalışmıyorsa veya ulaşılamıyorsa, uygulama çökmek yerine
    # hata basar ve producersız devam eder.
    logger.error(f"Kafka Producer başlatılırken hata oluştu: {e}")
    producer = None

# 3. FastAPI uygulamasını oluşturuyoruz
app = FastAPI()

# 4. Şehir listemiz aynı kalıyor
cities = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana", "Konya"]

# 5. /search endpoint'imiz güncelleniyor
@app.get("/search")
def search_index(term: str):
    timestamp = int(time.time() * 1000) # Unix zaman damgasını milisaniye cinsinden alıyoruz
    region = random.choice(cities) # Rastgele bir şehir seçiyoruz
    
    search_data = {
        "search": term,
        "timestamp": timestamp,
        "region": region
    }


    # Eğer producer bağlantısı başarılı bir şekilde kurulduysa...
    if producer:
        try:
            # Belirttiğimiz topic'e, search_data'yı değer olarak gönderiyoruz.
            producer.send('search-logs', value=search_data)
            logger.info(f"Mesaj başarıyla 'search-logs' topic'ine gönderildi: {search_data}")
        except KafkaError as e:
            # Mesaj gönderimi sırasında bir hata olursa hata mesajını basıyoruz
            logger.error(f"Kafka'ya mesaj gönderilirken hata oluştu: {e}")
    else:
        # Producer hiç başlatılamadıysa bilgilendirme yap
        logger.warning("Kafka Producer aktif değil, mesaj gönderilemedi.")

    logger.info(json.dumps(search_data, indent=2)) 
    return search_data

@app.get("/search/stream")
def search_stream(term: str):
    """
    Bu endpoint, sürekli olarak arama terimlerini dinler.
    """
    timestamp = datetime.now(time.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    region = random.choice(cities)  # Rastgele bir şehir seçiyoruz
    user_id = random.randint(1000, 2000)  # Rastgele bir kullanıcı ID'si oluşturuyoruz
    
    message = {
        "user_id": user_id,
        "search": term,
        "timestamp": timestamp,
        "region": region
    }

    STREAM_TOPIC_NAME = "search-analysis-stream"

    if producer:
        try:
            # Belirttiğimiz topic'e, message'ı değer olarak gönderiyoruz.
            producer.send(STREAM_TOPIC_NAME, value=message)
            logger.info(f"Mesaj başarıyla '{STREAM_TOPIC_NAME}' topic'ine gönderildi: {message}")
        except KafkaError as e:
            logger.error(f"Kafka'ya mesaj gönderilirken hata oluştu: {e}")
    else:
        logger.warning("Kafka Producer aktif değil, mesaj gönderilemedi.")

    # JSON formatında mesajı döndürüyoruz
    return {
        "message": "Mesaj gönderildi.", 
        "data": message
    }
