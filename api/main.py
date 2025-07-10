# 1. Gerekli kütüphaneleri import ediyoruz
from fastapi import FastAPI #type: ignore
from kafka import KafkaProducer #  Kafka Producer'ı import ediyoruz
from kafka.errors import KafkaError #  Olası Kafka hatalarını yakalamak için
import time
import random
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)  # Logger'ı ayarlıyoruz

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
        logger.info("Kafka Producer aktif değil, mesaj gönderilemedi.")

    logger.info(json.dumps(search_data, indent=2)) 
    return search_data