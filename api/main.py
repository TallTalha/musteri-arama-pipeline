# 1. Gerekli kütüphaneleri import ediyoruz
from fastapi import FastAPI
from kafka import KafkaProducer # YENİ: Kafka Producer'ı import ediyoruz
from kafka.errors import KafkaError # YENİ: Olası Kafka hatalarını yakalamak için
import time
import random
import json

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
    print("Kafka Producer bağlantısı başarıyla kuruldu.")
except KafkaError as e:
    # Eğer Kafka çalışmıyorsa veya ulaşılamıyorsa, uygulama çökmek yerine
    # hata basar ve producersız devam eder.
    print(f"Kafka Producer başlatılırken hata oluştu: {e}")
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
            print(f"Mesaj başarıyla 'search-logs' topic'ine gönderildi: {search_data}")
        except KafkaError as e:
            # Mesaj gönderimi sırasında bir hata olursa hata mesajını basıyoruz
            print(f"Kafka'ya mesaj gönderilirken hata oluştu: {e}")
    else:
        # Producer hiç başlatılamadıysa bilgilendirme yap
        print("Kafka Producer aktif değil, mesaj gönderilemedi.")

    print(json.dumps(search_data, indent=2)) 
    return search_data