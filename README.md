# Müşteri Arama Kayıtları Veri Boru Hattı

Bu proje, bir e-ticaret platformundaki arama olaylarını yakalayan, Kafka ile taşıyan ve Spark ile işleyen bir veri mühendisliği projesidir.

## Bileşenler
- **API:** FastAPI ile yazılmış, arama olaylarını alıp Kafka'ya üreten servis.
- **Mesajlaşma:** Apache Kafka
- **İşleme:** Apache Spark (Batch & Streaming)
- **Depolama:** MongoDB & Elasticsearch

![A flowchart diagram showing the architecture of a customer search data pipeline. The diagram includes labeled components: Front-end Search Box JSON Data, Back-end FAST API Producer, Apache Kafka topic search-logs Listener, Apache Spark Spark Job Batch Process, Apache Spark Stream Instant Data Analysis, and MongoDB NoSQL. Arrows indicate the flow of data between these components. The environment is technical and structured, with a neutral and informative tone. Additional labels include Digital Ocean Droplet and Müşteri Arama Pipeline at the top.](images/flow.svg)
