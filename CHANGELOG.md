# 📝 Changelog

Tüm önemli değişiklikler bu dosyada belgelenir.
Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) ve [Semantic Versioning](https://semver.org/) uyumludur.

---

## [1.0.0] - 2026-10-20

### Added
- **Scanner Engine**: `~/.gemini/antigravity/brain` dizinindeki 114+ Antigravity oturumunun taranması ve geçerli konuşmaların filtrelenmesi.
- **DAG Converter**: Antigravity kronolojik adımlarını Claude Code'un `uuid`/`parentUuid` düğüm ağacına ve trailing `last-prompt` yapısına dönüştüren motor.
- **Proje Dizini Çözücü**: Tool call ve transcript yollarını frekans analiziyle tarayarak oturumun ait olduğu gerçek repo yolunu belirleyen algoritma.
- **Tek Tık Standalone EXE**: PyInstaller ile derlenmiş taşınabilir `AntigravityToClaude.exe`.
- **Interaktif CLI & Runner**: Renkli özet tablosu sunan ve çift tıklandığında otomatik çalışan `run.bat` ve `cli.py`.
- **Tarihçe Entegrasyonu**: Aktarılan tüm oturumların `~/.claude/history.jsonl` dosyasına eklenmesi ve `claude --resume` seçicisinde doğrudan listelenmesi.
- **Birim Testleri**: Slugify, prompt temizleme ve DAG dönüşümü için kapsamlı testler (`test_migration.py`).
