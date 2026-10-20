# 🚀 AntigravityToClaude

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform: Windows / Linux / macOS](https://img.shields.io/badge/Platform-Cross--Platform-brightgreen.svg)]()
[![Build: Standalone EXE](https://img.shields.io/badge/Release-One--Click%20EXE-orange.svg)]()
[![Claude Code: Compatible](https://img.shields.io/badge/Claude%20Code-DAG%20Sessions-purple.svg)]()

> **Google DeepMind Antigravity sohbet kayıtlarını tek tıkla yerel Anthropic Claude Code oturumlarına dönüştüren ve entegre eden açık kaynaklı köprü aracı.**

---

## ⚡ Neden AntigravityToClaude?

Antigravity, oturumlarını `~/.gemini/antigravity/brain/<id>` altında karmaşık JSONL adımları, dahili XML etiketleri (`<USER_REQUEST>`, `<ADDITIONAL_METADATA>`) ve araç çağrıları olarak saklar.

**AntigravityToClaude** bu kayıtları otomatik tarar:
1. **XML & Sistem Gürültüsünü Temizler**: Promptları saf metne dönüştürür.
2. **Proje ve Çalışma Alanını Otomatik Tespit Eder**: Araç çağrılarındaki dosya yollarından projenin gerçek dizinini (`GitHub/Public/...`) bularak doğru Claude slug'ına bağlar.
3. **Claude Code DAG Mimarisi İnşa Eder**: `uuid`, `parentUuid` hiyerarşisi kurar ve oturumu `last-prompt` ile tamamlar.
4. **Geçmişe Ekler**: `~/.claude/history.jsonl` kütüğüne kaydederek `claude --resume` seçicisinde doğrudan görünmesini sağlar.
5. **Tek Tıkla Çalışır**: PyInstaller ile derlenmiş taşınabilir `.exe` sayesinde hiçbir kurulum yapmadan çift tıkla tüm sohbetleri anında aktarır.

---

## 🚀 Hızlı Başlangıç

### Seçenek 1: Tek Tıkla Çalıştır (Windows .exe)
1. `AntigravityToClaude.exe` dosyasını indirin veya çalıştırın.
2. Konsol penceresinde tüm Antigravity sohbetleriniz otomatik taranır ve Claude Code'a aktarılır.
3. Terminalde `claude --resume` yazarak istediğiniz sohbeti kaldığı yerden devam ettirin!

### Seçenek 2: Kaynak Koddan Çalıştırma (Python)
```bash
# Bağımlılık gerektirmez (Saf Python 3.9+)
git clone https://github.com/halilogia/AntigravityToClaude.git
cd AntigravityToClaude

# Tüm sohbetleri aktar
python main.py

# Veya çift tıkla: run.bat
```

---

## 🛠️ CLI Kullanımı ve Parametreler

```bash
# Yalnızca tespit edilen sohbetleri listele
python main.py --list

# Dosya yazmadan simülasyon yap (Önizleme)
python main.py --dry-run

# Belirli bir sohbet ID'sini aktar
python main.py --id <CONVERSATION_ID>

# Önceden aktarılan oturumların üzerine zorla yaz
python main.py --force
```

---

## 📚 Çekirdek Dokümantasyon

| Belge | Açıklama |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | DAG dönüşümü, slugify ve dosya mimarisi |
| [ROADMAP.md](ROADMAP.md) | Sürüm aşamaları ve gelecek hedefleri |
| [CHANGELOG.md](CHANGELOG.md) | SemVer sürüm geçmişi |
| [KNOWLEDGE.md](KNOWLEDGE.md) | Mühendislik hafızası ve Claude Code mimari notları |
| [TASKS.md](TASKS.md) | Aktif görev takibi |
| [SKILLS.md](SKILLS.md) | Antigravity ve Claude Code beceri kılavuzu |
| [LICENSE](LICENSE) | GNU General Public License v3.0 (GPL-3.0) |

---

## ⚖️ Lisans

Bu proje **GNU General Public License v3.0 (GPL-3.0)** altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.
