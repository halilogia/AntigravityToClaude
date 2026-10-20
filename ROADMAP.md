# 🗺️ Roadmap & Kilometre Taşları

AntigravityToClaude geliştirme planı ve gelecek sürümler.

---

## 🚀 v1.0.0 (MVP - Tamamlandı)
- [x] Antigravity `brain/` dizini otomatik tarayıcısı (`scanner.py`).
- [x] XML ve sistem etiketleri temizleyicisi (`clean_prompt_text`).
- [x] Araç çağrılarından otomatik çalışma alanı / proje dizini tespiti (`detect_project_dir`).
- [x] Claude Code DAG ağacı inşası (`uuid`, `parentUuid`, `last-prompt`).
- [x] Claude Code proje slugify algoritması (`slugify_project_path`).
- [x] `~/.claude/history.jsonl` otomatik oturum kaydı.
- [x] Çift tıkla çalışan interaktif konsol arayüzü (`cli.py`, `run.bat`).
- [x] Windows için tek dosyalı PyInstaller standalone `.exe` derlemesi (`AntigravityToClaude.exe`).
- [x] Birim testleri (`tests/test_migration.py`).

---

## ⏳ v1.1.0 (Aktif Sprint)
- [ ] Tersine aktarım (Claude Code oturumlarını Antigravity formatına çevirme desteği).
- [ ] ChatGPT Web / OpenAI Codex oturum formatlarına ihracat köprüleri.
- [ ] Çoklu iş parçacıklı (multithreaded) toplu tarama hızlandırıcısı.
- [ ] Web arayüzü (Minimal yerel dashboard ile oturumları inceleme).

---

## 🔮 v2.0.0 (Gelecek Vizyon)
- [ ] Evrensel Ajan Sohbet Formatı (Universal Agent Transcript Standard - UATS).
- [ ] Otomatik semantik özet çıkarma ve oturum içi anahtar kelime arama.
- [ ] Farklı oturumlar arasındaki araç ve kod parçası bağımlılık grafiği.
