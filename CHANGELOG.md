# 📝 Changelog

Tüm önemli değişiklikler bu dosyada belgelenir.
Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) ve [Semantic Versioning](https://semver.org/) uyumludur.

---

## [1.2.0] - 2026-10-21

### Added
- **Claude Code 2.1 Doğal DAG Mimarisi**: `tool_use` (assistant) ve `tool_result` (user) düğüm çiftleri entegre edildi. `run_command` -> `Bash`, `read_file` -> `View`, `write_file` -> `Write`, `edit_file` -> `Edit` eşleşmeleri kodlandı.
- **`ai-title` Düğüm Entegrasyonu**: Claude Code TUI pencere başlığı ve oturum seçicisi için `.jsonl` başına resmi `ai-title` düğümleri eklendi.
- **SQLite & Laptop Oturum Senkronizasyonu**: `conversation_summaries.db` üzerinden orijinal başlıklar, gerçek tarihler ve laptop çalışma alanları içe aktarıldı; `TITLE_OVERRIDES` tablosu bağlandı.

### Fixed
- **Sistem İzin Dökümü & XML Sızıntısı Giderildi**: `Your current permission grants`, `Created At...`, `<USER_SETTINGS_CHANGE>`, terminal durum logları ve araç onay mesajları filtrelenerek sohbet metninden tamamen temizlendi.
- **Düşünce Zinciri (Thinking) İzolasyonu**: Ham metin blokları yerine yerel `thinking` blokları kullanılarak TUI arayüzünün temiz ve katlı kalması sağlandı.
- **Boşluklu Dizin Yolu Çözümleme**: `detect_project_dir` fonksiyonunda boşluk içeren Windows kullanıcı yolları (`Halil Emre`) düzeltildi.

## [1.1.0] - 2026-10-21

### Fixed
- **Claude Code 2.1+ Resume Uyumluluğu**: Dönüştürülen `.jsonl` dosyalarına `sessionId`, `cwd`, `version` ("2.1.306"), `isSidechain` ve `queue-operation` kayıtları eklenerek Claude Code'un `claude --resume <id>` komutuyla oturumları %100 sorunsuz geri yüklemesi sağlandı.

## [1.0.0] - 2026-10-20

### Added
- **Scanner Engine**: `~/.gemini/antigravity/brain` dizinindeki 114+ Antigravity oturumunun taranması ve geçerli konuşmaların filtrelenmesi.
- **DAG Converter**: Antigravity kronolojik adımlarını Claude Code'un `uuid`/`parentUuid` düğüm ağacına ve trailing `last-prompt` yapısına dönüştüren motor.
- **Proje Dizini Çözücü**: Tool call ve transcript yollarını frekans analiziyle tarayarak oturumun ait olduğu gerçek repo yolunu belirleyen algoritma.
- **Tek Tık Standalone EXE**: PyInstaller ile derlenmiş taşınabilir `AntigravityToClaude.exe`.
- **Interaktif CLI & Runner**: Renkli özet tablosu sunan ve çift tıklandığında otomatik çalışan `run.bat` ve `cli.py`.
- **Tarihçe Entegrasyonu**: Aktarılan tüm oturumların `~/.claude/history.jsonl` dosyasına eklenmesi ve `claude --resume` seçicisinde doğrudan listelenmesi.
- **Birim Testleri**: Slugify, prompt temizleme ve DAG dönüşümü için kapsamlı testler (`test_migration.py`).
