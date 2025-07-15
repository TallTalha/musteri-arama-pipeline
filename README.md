Müşteri Arama Kayıtları - Veri Mühendisliği Boru Hattı Projesi 🚀

Bu proje, modern veri mühendisliği araçlarını kullanarak bir e-ticaret platformundaki kullanıcı arama olaylarını yakalayan, işleyen ve analiz eden uçtan uca bir veri boru hattıdır.

1. Projenin Amacı

Bu projenin temel amacı, bir e-ticaret platformunda kullanıcıların yaptığı arama sorgularını anlık (real-time) ve toplu (batch) olarak analiz etmektir. Toplanan verilerle, aşağıdaki gibi iş sorularına veri odaklı cevaplar aranır:

    Hangi ürünler anlık olarak trend oluyor?

    Günün hangi saatlerinde arama yoğunluğu artıyor?

    Hangi kullanıcı hangi ürünlerle daha çok ilgileniyor?

    Kullanıcı davranışlarına göre kişiselleştirilmiş deneyimler nasıl sunulur?

Bu proje, bu soruları cevaplamak için gerekli olan veri altyapısını kurma ve işletme süreçlerini kapsar.

2. Mimari ve Veri Akışı

Proje, endüstri standardı olan, ayrıştırılmış (decoupled) ve ölçeklenebilir bir mimari üzerine kurulmuştur. Veri akışı aşağıdaki gibidir:

![A flowchart diagram showing the architecture of a customer search data pipeline. The diagram includes labeled components: Front-end Search Box JSON Data, Back-end FAST API Producer, Apache Kafka topic search-logs Listener, Apache Spark Spark Job Batch Process, Apache Spark Stream Instant Data Analysis, and MongoDB NoSQL. Arrows indicate the flow of data between these components. The environment is technical and structured, with a neutral and informative tone. Additional labels include Digital Ocean Droplet and Müşteri Arama Pipeline at the top.](images/flow.svg)

    Veri Üretimi (data_generator.py / API): Kullanıcı arama olayları, gerçekçi bir dağılım ve zaman serisiyle simüle edilir. Her arama, bir JSON mesajı olarak oluşturulur.

    Veri Taşıma (Apache Kafka): Üretilen bu JSON mesajları, yüksek hacimli veri akışını kayıpsız ve gecikmesiz bir şekilde yönetebilen Kafka'daki topic'lere gönderilir (produce).

    Veri İşleme (Apache Spark):

        Batch İşleme: Periyodik olarak çalışan Spark işleri, Kafka'da birikmiş verileri toplu olarak okur, üzerinde agregasyon ve pivot gibi karmaşık analizler yapar. (Örn: pivot_analysis.py)

        Streaming İşleme: Sürekli çalışan Spark işleri, Kafka'ya veri geldiği anda onu yakalar, anlık filtreleme ve basit dönüşümler yapar. (Örn: streaming_consumer.py)

    Veri Depolama (MongoDB): Spark tarafından işlenip anlamlı hale getirilen analiz sonuçları (örn: pivot tablolar, trend raporları), daha sonra dashboard'larda kullanılmak veya başka servisler tarafından okunmak üzere MongoDB'ye yazılır.

3. Kullanılan Teknolojiler

    Veri Akışı ve Mesajlaşma: Apache Kafka

    Veri İşleme: Apache Spark 3.5.1 (PySpark)

    Veri Depolama: MongoDB

    API Servisi: Python, FastAPI, Uvicorn

    Veri Üretimi (Simülasyon): Python, Faker, kafka-python

    Altyapı: DigitalOcean Ubuntu Sunucu 24.04

    Gözlemlenebilirlik (Logging): Python logging modülü

    Arayüz ve Yönetim: MongoDB Compass

    Versiyon Kontrolü: Git & GitHub

4. Proje Yapısı

Proje, her birinin kendi sorumluluğu ve sanal ortamı olan modüler bir yapıda organize edilmiştir:
```
musteri-arama-pipeline/
├── api/                  # FastAPI uygulaması ve bağımlılıkları
│   ├── venv-api/
│   └── main.py           # Backend API simülasyonudur, FastAPI kullanılır.         
├── data-generator/       # Test verisi üretici script'i
│   ├── venv-gen/
│   └── data_generator.py # user_id,search-term,region, timestamp gibi bilgileri rastgele üretir
├── spark-consumer/       # Spark işleri (batch ve streaming)
│   ├── venv-spark/
│   ├── batch_consumer.py # search-logs topiğindeki verileri çeker ve mongodb'ye yazar
│   ├── pivot_analysis.py # user_id bazında pivot işlemleri yapar ve mongodb'ye yazar
│   ├── realtime_tracker.py # anlık verileri kafkadan çeker sonra filtreler ve mongodb'ye yazar
│   ├── streaming_consumer.py # anlık verileri kafkadan çeker ve mongodb'ye yazar
│   └── trending_topic_analysis.py # günlük verileri 30 dakikalık dilimlere böler ve mongodb'ye yazar
├   
├── utils/                # Yardımcı modüller (örn: merkezi logger)
│   └── logger.py         #Logging modülüdür, logging kütüphanesi kullanılır
├── logs/                 # Log dosyalarının tutulduğu klasör (git'e dahil değil)
├── checkpoint/           # Spark Streaming checkpoint'leri (git'e dahil değil)
├── .gitignore
└── README.md
```
5. Kurulum ve Çalıştırma

Bu projeyi çalıştırmak için sunucu tarafında ve yerel tarafta belirli adımların izlenmesi gerekir.

Ön Gereksinimler

    Sunucuda Java, Python3, venv ve git kurulu olmalıdır.

    Sunucuda Apache Kafka, Apache Spark, MongoDB ve Elasticsearch/Kibana servisleri çalışır durumda olmalıdır.

Çalıştırma Adımları

    Kod Senkronizasyonu:

        Yerel PC: git clone https://github.com/TallTalha/musteri-arama-pipeline.git

        Sunucu: Aynı git clone komutu ile projeyi sunucuya da klonlayın. Geliştirme döngüsünde git pull ile güncelleyin.

    Bağımlılıkların Kurulumu: Projedeki her alt klasör (api, data-generator, spark-consumer) için kendi venv'ini oluşturun ve pip install -r requirements.txt ile bağımlılıkları kurun. (Not: Henüz requirements.txt dosyaları oluşturmadık, bu bir sonraki best practice adımı olabilir!)

    Veri Boru Hattını Çalıştırma:

        [KENDİ PC'NDE - Terminal 1]: Uzak sunucudaki servislere erişim için SSH tünelini başlat: ssh sunucum

        [SUNUCUDA - Terminal 2]: Veriyi anlık olarak işleyecek olan Spark Streaming işini başlat: sudo spark-submit ... spark-consumer/streaming_consumer.py

        [KENDİ PC'NDE - Terminal 3]: Veri üretecek olan API servisini başlat: uvicorn api.main:app ...

        [Tarayıcı/Postman]: API'ye (http://localhost:8080/search/stream) istekler göndererek tüm hattı uçtan uca test et.


