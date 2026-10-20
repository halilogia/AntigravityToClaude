# 🛠️ Skills & Operational Rules

AntigravityToClaude projesinde geliştirme ve operasyon yaparken uyulması gereken kurallar.

---

## 🎯 Proje Misyonu
Antigravity sohbet kayıtlarının kayıpsız, yüksek doğruluklu ve tek tıkla Claude Code oturumlarına aktarılmasını sağlamak.

---

## 📜 Temel Geliştirme Kuralları

1. **Harici Bağımlılık Yasağı (Zero External Runtime Dependencies)**:
   - `AntigravityToClaude` çekirdek kütüphaneleri yalnızca standart Python 3 kütüphanelerini (`os`, `sys`, `json`, `re`, `uuid`, `time`, `datetime`, `argparse`, `unittest`) kullanır.
   - Hiçbir çalışma zamanı harici `pip` paketi eklenmez. Yalnızca dağıtım derlemesi için `pyinstaller` kullanılır.

2. **Geriye Dönük Uyumluluk**:
   - Hem eski Antigravity formatları (basit step listeleri) hem de yeni çoklu araç çağrılı karmaşık oturumlar desteklenir.
   - Claude Code'un `uuid`/`parentUuid` ağaç yapısı bozulamaz.

3. **Güvenli Dosya İşlemleri**:
   - `~/.gemini/antigravity/brain` dizini yalnızca salt-okunur (`r`) olarak açılır. Kaynak dosyalarda silme veya değişiklik yapılamaz.
   - `~/.claude/history.jsonl` dosyasında sadece oturum bulunmuyorsa ekleme (`append`) yapılır; mevcut kayıtlar korunur.

4. **Definition of Done (DoD)**:
   - Tüm birim testleri yeşil olmalıdır (`python -m unittest discover tests`).
   - PyInstaller derlemesi temiz tamamlanmalıdır (`pyinstaller --onefile ...`).
   - 8 Core Docs belgesinin hiçbiri 200 satırı aşmamalıdır.
