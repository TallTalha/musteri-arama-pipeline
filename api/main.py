# 1. Gerekli kütüphaneleri import ediyoruz
from fastapi import FastAPI
import time
import random
import json

# 2. FastAPI uygulamasını oluşturuyoruz.
app = FastAPI()

# 3. Şehirleri simüle etmek için bir liste oluşturalım
cities = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana", "Konya"]

# 4. /search endpoint'ini tanımlıyoruz. 
@app.get("/search")
def search_index(term: str):
    # FastAPI, term: str yazdığımızda, 'term' adında bir parametre beklediğini
    # anlar. 

    # 5. Zaman damgası ve rastgele şehir oluşturuyoruz
    timestamp = int(time.time() * 1000) # Milisaniye cinsinden zaman damgası
    region = random.choice(cities)      # Rastgele bir şehir seçer

    # 6. JSON objesini oluşturalım. Harici kütüphaneye gerek yok.
    # Bu JSON objesi, arama terimi, zaman damgası ve bölgeyi içerir.
    # Bu, API'nin döneceği veriyi temsil eder.
    search_data = {
        "search": term,
        "timestamp": timestamp,
        "region": region
    }

    # 7. Sonucu konsola JSON formatında yazdıralım 
    # indent=2, çıktıyı daha okunaklı yapar.
    print(json.dumps(search_data, indent=2))

    # 8. API'nin kendisi de bu JSON objesini geri dönsün.
    # Bu, tarayıcıda veya Postman'de sonucu görmemizi sağlar.
    return search_data
