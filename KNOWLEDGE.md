# 🧠 Engineering Knowledge & Architecture Decisions

AntigravityToClaude kalıcı mühendislik hafızası ve oturumlar arası kararlar.

---

## 🏛️ Mimari Kararlar (ADR)

### [ADR-01] Claude Code DAG Ağacı & last-prompt Zorunluluğu
- **Karar**: Claude Code, JSONL oturum dosyalarında konuşmaları doğrusal dizi yerine bir Yönlü Döngüsüz Çizge (DAG) olarak okur. İlk düğüm `parentUuid: null` olmalı ve son düğüm `last-prompt` tipiyle en son asistan düğümünü işaret etmelidir (`leafUuid`).
- **Neden**: Bu marker bulunmadığında Claude Code "No deferred tool marker found" hatası verir veya oturumu başa sarar.

### [ADR-02] Proje Slugify Standartı
- **Karar**: Claude Code proje dizinlerini `projects/<slug>` altında saklar. Sürücü iki tire (`C--`), tüm ters eğik çizgi, düz eğik çizgi ve boşluklar ise tek tire (`-`) ile temsil edilir.
- **Kanıt**: `~/.claude/projects/C--Users-Halil-Emre-Desktop-GitHub-Public-LifeOS`

### [ADR-03] UTF-8 Console Fallback (Windows cp1252 / cp1254)
- **Karar**: Windows komut satırlarında `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` zorunlu kılınmıştır ve banner kutu çizimleri standart ASCII (`+---`, `|`) karakterlere uyarlanmıştır.
- **Neden**: Windows varsayılan OEM kod sayfalarında Unicode kutu karakterleri `UnicodeEncodeError` patlamasına yol açar.

### [ADR-04] Safe-Skip ve Idempotent Koruma (Yeni Sohbetleri Korumak)
- **Karar**: Bir oturum `~/.claude/projects/<slug>/<sessionId>.jsonl` altında zaten mevcutsa, program varsayılan olarak bu oturumu atlar (`already_exists`).
- **Neden**: Kullanıcı Antigravity'den aktarılan oturumu Claude Code'da açıp yeni mesajlar yazdığında, program 2. kez çalıştırılsa bile Claude Code'daki yeni konuşmalar asla ezilmez, silinmez ve eskiye dönmez. Yalnızca `--force` bayrağı ile üzerine yazılabilir.

---

## ⚠️ Tekrarlayan Tuzaklar (Gotchas)

### [GOTCHA-01] Çift Tık Konsolunun Erken Kapanması
- Windows'ta bir `.bat` veya `.exe` çift tıklandığında Python işlemi bitince pencere 0 ms içinde kapanır.
- **Çözüm**: `cli.py` içerisinde `sys.stdin.isatty()` kontrolü ile oturum bitiminde `input("Çıkmak için Enter'a basın...")` bekletilir.

### [GOTCHA-02] Boş Adımlı Trajectory Klasörleri
- Antigravity, kullanıcı henüz mesaj yazmadan yeni sohbet penceresi açtığında boş `brain/<id>` klasörü üretir.
- **Çözüm**: `scanner.py`, `step_count == 0` veya `turn_count == 0` olan oturumları tespit eder ve temiz şekilde `skipped` statüsüne alır.
