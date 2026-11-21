# EVQ Smart Charging — Proje Gelişimi 1

**Bitirme projesi bağlantısı:** Önceki EVQ Station kablosuz şarj yönetim sistemi fikri temel alınarak yazılım mimarisinin genişletilmesi amaçlanmıştır.

**Problem:** Farklı şarj cihazları, ücret tarifeleri ve oturum durumları tek bir program içinde iç içe yazıldığında sistemin genişletilmesi ve test edilmesi zorlaşır.

**Çözüm:** Python ile iki sanal şarj ünitesi, ücretlendirme stratejileri, şarj oturumu durumları ve SQLite kayıtları geliştirilmiştir. Flutter istemcisi bu simülasyonun durumunu gösterir ve işlem başlatma/durdurma isteklerini iletir.

**Tasarım kalıpları:**
1. **Factory Method (Yaratımsal):** Farklı şarj denetleyicilerinin oluşturulması.
2. **Adapter (Yapısal):** Uyumsuz cihaz komutlarının ortak arabirime uyarlanması.
3. **Strategy (Davranışsal):** Ücret hesaplama algoritmalarının bağımsız değiştirilmesi.
4. **State (Davranışsal):** Şarj oturumu durum geçişlerinin kontrol edilmesi.

**Test ve kurulum:** `README.md` dosyasında kurulum, çalıştırma ve API örnekleri bulunmaktadır. `backend/tests/test_patterns.py` içinde otomatik testler hazırlanmıştır.

**Açık sınırlar:** Fiziksel şarj, gerçek ödeme, QR taraması ve gerçek AI/ResNet50 entegrasyonu bu sürümde yoktur. Flutter derlemesi bir Flutter SDK ortamında ayrıca doğrulanmalıdır. AI destekli geliştirme kullanımı proje raporunda açıklanmalıdır.
