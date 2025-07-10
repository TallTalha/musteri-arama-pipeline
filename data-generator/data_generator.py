import json
import random
from time import sleep 
from datetime import datetime, timezone, timedelta
from faker import Faker
from kafka import KafkaProducer
from kafka.errors import KafkaError

def generate_random_timestamp_iso():
    """Rastgele bir ISO 8601 zaman damgası üretir."""
    today = datetime.now(timezone.utc)
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)

    random_seconds = random.randint(0, 24 * 60 * 60 - 1)  # Gün içindeki saniyeler

    random_datetime = start_of_day + timedelta(seconds=random_seconds)

    return random_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')


faker = Faker('tr_TR')  # Türkçe yerel ayar

try:
    producer = (
        KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    )
except KafkaError as e:
    print(f"Kafkaya bağlanırken hata oluştu: {e}")
    exit()

search_terms = [
    "telefon", "bilgisayar", "tablet", "kamera", "televizyon",
    "yazıcı", "kulaklık", "hoparlör", "akıllı saat", "oyuncu ekipmanları" 
    ]

weights = [ random.randint(1, 20) for _ in search_terms ]


TOPIC_NAME = "search-analysis-userid"
VERI_SAYISI = 30000
print(f"Kafkaya bağlanıldı. Topic: {TOPIC_NAME}. Veri sayısı: {VERI_SAYISI} veri üretilecek.")
      
for i in range(VERI_SAYISI):
    user_id = random.randint(1000, 2000)
    search_term = random.choices(search_terms, weights=weights, k=1)[0]
    region = faker.city()
    timestamp = generate_random_timestamp_iso()

    message = {
        "user_id": user_id,
        "search": search_term,
        "region": region,
        "timestamp": timestamp
    }

    try:
        producer.send(TOPIC_NAME, value=message)
        if i % 1000 == 0:
            print(f"{i} veri gönderildi.")
    except KafkaError as e:
        print(f"Mesaj gönderilirken hata oluştu: {e}")
        continue
    sleep(0.01)  # 10ms bekleme, Kafka'ya aşırı yük bindirmemek için

producer.flush()  # Tüm mesajların gönderilmesini bekle
print("Tüm veriler Kafka'ya gönderildi.")
producer.close()  # Üreticiyi kapat
print("Kafka üreticisi kapatıldı.")
