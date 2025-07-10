import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# dirname ile bir üst dizine çıkarız, iki kere kullanıp ana dizine ulaşırız
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs') # Ana dizindeki logs klasörüne erişiriz

os.makedirs(LOG_DIR, exist_ok=True) # Ana dizinde logs klasörü yoksa oluştururuz

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Logger'ı ayarlar ve döndürür.
    Args:
        name (str): logs klasörü altındaki log dosyasının adını belirler.
        level (int): Log seviyesini belirler. Varsayılan INFO seviyesidir.
        log_file (str): Opsiyonel. Belirtilmezse, logs/{name}.log yolunu kullanır.
    Returns:
        logging.Logger: Ayarlanmış logger nesnesi.
    """
    #(1) Her logger için ayrı bir dosya yolu oluştururuz
    log_file = os.path.join(LOG_DIR, f"{name}.log")

    #(2) Log Mesajlarının formatını tanımlarız
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #(3) RotatingFileHandler ile log dosyasının kontrolsüzce büyümesini engelleriz
    # Büyüyen log dosyalarını 10 MB boyutuna gelince app.log.x uzantılı dosyalara döneriz
    # Maksimum 5 yedek dosya tutarız
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(log_format)  # Formatı dosya handler'ına uygularız

    #(4) Konsol çıktısı için de bir handler ekleriz
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)  # Formatı konsol handler'ına uygular

    #(5) Logger Oluşturma
    logger = logging.getLogger(name)  # name parametresine göre bir logger oluştururuz
    logger.setLevel(level)  # level parametresine göre log seviyesini ayarlarız

    #(6) logger'ın zaten handler'ı varsa yeni handler eklemeyiz
    # Böylece her seferinde yeni handler eklenmez, bu da performansı artır
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger  # Ayarlanmış logger'ı döndürürüz

