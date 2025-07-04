# Müşteri Arama Kayıtları Veri Boru Hattı

Bu proje, bir e-ticaret platformundaki arama olaylarını yakalayan, Kafka ile taşıyan ve Spark ile işleyen bir veri mühendisliği projesidir.

## Bileşenler
- **API:** FastAPI ile yazılmış, arama olaylarını alıp Kafka'ya üreten servis.
- **Mesajlaşma:** Apache Kafka
- **İşleme:** Apache Spark (Batch & Streaming)
- **Depolama:** MongoDB & Elasticsearch
