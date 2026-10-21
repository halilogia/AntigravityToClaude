"""
scanner.py - Scans Antigravity brain directories, parses SQLite metadata, and discovers conversation trajectories.
"""

import os
import json
import re
import sqlite3
from typing import List, Dict, Any, Optional

TITLE_OVERRIDES = {
    "2b3a9827-4401-461f-b26a-88b262029dfa": "KPSS Reels Mobil Uygulaması",
    "23b92a38-cb1f-4573-b41e-3fcae439cee2": "Chrome Eklentisi Gereksinim ve Mimari Analizi",
    "65fa4254-5785-44c5-8d4d-6365ce5c3e16": "Flutter KPSS Roadmap Temizliği & Güncellemesi",
    "746cd31d-9f4a-44cb-be22-763e90c145c3": "ÖSYM Tarih Soruları Git Yükleme",
    "91d2b84c-8471-4c01-94a6-9fe0ec124c06": "Terminal Bash Hata Analizi ve Çözümü",
    "af4b623d-d163-4a72-a958-7b7c19cb9fb9": "KPSS Harita Topic İsimlendirme Düzeltmesi",
    "b45d9b4f-5dc9-45a1-9710-438a56e2b04a": "Metin Kutularından Taşan İçeriklerin Düzeltilmesi",
    "b9ed7456-920a-4c54-9811-fcd8f780e69f": "Konu Dağılımı ve Çalışma Takibi Sıralama Ayarları",
    "c03232ad-2de1-43a2-be58-4a6a95dbd121": "Arayüz Metin Hizalama ve Ortalama Düzenlemesi",
    "e2afc1ed-97aa-4a28-8287-e9a85c500225": "Çift Bilgisayar Geliştirme Ortamı & Git Senkronizasyonu",
    "f6c61cf0-392e-4eeb-9533-dc4d72456424": "KPSS Quiz Ekranı Süre Sayacı Entegrasyonu",
    "fc84610d-0c8a-4d6b-bbc8-64f9b6d55b3d": "KPSS Coğrafya Haritalar Tam Ekran İnteraktif Öğrenme Oyunu",
    "fe2336b5-0aa4-47d5-bcd6-56e2eb5d34a5": "KPSS Kod Tabanı Hata Giderme ve Stabilizasyon"
}

def get_brain_dir() -> str:
    """Returns the default Antigravity brain directory across platforms."""
    custom = os.environ.get("ANTIGRAVITY_BRAIN_DIR")
    if custom and os.path.isdir(custom):
        return custom
    return os.path.expanduser(os.path.join("~", ".gemini", "antigravity", "brain"))

def get_claude_dir() -> str:
    """Returns the default Claude Code configuration directory."""
    custom = os.environ.get("CLAUDE_DIR")
    if custom and os.path.isdir(custom):
        return custom
    return os.path.expanduser(os.path.join("~", ".claude"))

def clean_prompt_text(raw_text: str) -> str:
    """Strips internal XML tags, permission tables, and formatting noise from prompt content."""
    if not raw_text or not isinstance(raw_text, str):
        return ""
    text = raw_text
    # 1. Strip USER_SETTINGS_CHANGE blocks and unclosed tags
    text = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*?</USER_SETTINGS_CHANGE>\s*', '', text)
    text = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*$', '', text)
    text = re.sub(r'</?USER_SETTINGS_CHANGE>\s*', '', text)

    # 2. Strip metadata blocks including their inner contents
    text = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>\s*', '', text)
    text = re.sub(r'<CONTEXT_SUMMARY>[\s\S]*?</CONTEXT_SUMMARY>\s*', '', text)
    text = re.sub(r'<SYSTEM_MESSAGE>[\s\S]*?</SYSTEM_MESSAGE>\s*', '', text)
    text = re.sub(r'</?USER_REQUEST[^>]*>', '', text)

    # 3. Strip nested system context blocks if present
    text = re.sub(r'<user_information>[\s\S]*?</user_information>\s*', '', text)
    text = re.sub(r'<system_information>[\s\S]*?</system_information>\s*', '', text)
    text = re.sub(r'<conversation_transcript>[\s\S]*?</conversation_transcript>\s*', '', text)
    text = re.sub(r'<skills>[\s\S]*?</skills>\s*', '', text)
    text = re.sub(r'<guidelines>[\s\S]*?</guidelines>\s*', '', text)

    # 4. Strip system permissions dump table and status logs
    text = re.sub(r'(?i)Your current permission grants[\s\S]*?(?=(?:\n\n|\Z|Jump to bottom|\*\*))', '', text)
    text = re.sub(r'(?m)^\s*-\s*[a-zA-Z0-9_]+\([^)]*\):\s*(?:allowed|ask|denied)\s*$', '', text)
    text = re.sub(r'(?i)Jump to bottom[^\n]*', '', text)
    text = re.sub(r'(?i)Created At:\s*[\d\-:TZ]+\s*Completed At:\s*[\d\-:TZ]+', '', text)

    # 5. Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_smart_title(raw_text: str) -> str:
    """Extracts a clean, human-friendly title from a raw prompt."""
    cleaned = clean_prompt_text(raw_text)
    if not cleaned:
        return ""
    t = re.sub(r'[*_`#~>]', ' ', cleaned)
    t = re.sub(r'^\s*\d+[\.\)]\s*', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    parts = re.split(r'[:;?!.]\s+', t)
    chosen = parts[0] if parts else t
    if len(chosen) < 15 and len(parts) > 1:
        chosen = f"{parts[0]}: {parts[1]}"
    if len(chosen) > 55:
        cut = chosen[:55]
        if ' ' in cut:
            cut = cut.rsplit(' ', 1)[0]
        chosen = cut + '...'
    return chosen.strip()

def load_conversation_db_metadata() -> Dict[str, Dict[str, Any]]:
    """Reads titles, timestamps, and workspace mappings from Antigravity SQLite database."""
    db_path = os.path.expanduser(os.path.join("~", ".gemini", "antigravity", "conversation_summaries.db"))
    if not os.path.exists(db_path):
        return {}
    meta: Dict[str, Dict[str, Any]] = {}
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT conversation_id, title, last_modified_time, workspace_uris FROM conversation_summaries")
        for cid, title, last_mod, uris in c.fetchall():
            meta[cid] = {
                "title": (title or "").strip(),
                "last_modified": last_mod,
                "workspace_uris": uris or ""
            }
        conn.close()
    except Exception:
        pass
    return meta

def extract_path_candidates(val: str) -> List[str]:
    """Extracts valid Windows file and folder paths, preserving spaces in folder names."""
    if not isinstance(val, str) or not val:
        return []
    cleaned = val.strip().strip('"\'')
    if len(cleaned) > 2 and cleaned[1] == ':' and cleaned[2] in ('\\', '/'):
        return [cleaned]
    if cleaned.startswith("file:///"):
        return [cleaned[8:]]
    # Find Windows paths with drive letter, supporting spaces in directory names
    matches = re.findall(r'[A-Za-z]:\\[^"\'<>:|?*\r\n\t]+', val)
    return [m.rstrip(' .,;') for m in matches]

def detect_project_dir(transcript_path: str, default_fallback: str, db_workspace_uris: str = "") -> str:
    """
    Analyzes SQLite workspace uris, tool calls, file paths, and environment hints in the transcript
    to find the true project/workspace root.
    """
    # 1. First priority: Check SQLite workspace URIs (includes laptop mappings)
    if db_workspace_uris:
        try:
            uris = json.loads(db_workspace_uris) if db_workspace_uris.startswith("[") else [db_workspace_uris]
            for u in uris:
                if isinstance(u, str) and u.startswith("file:///"):
                    clean_p = u[8:]
                    if len(clean_p) > 2 and clean_p[1] == ':':
                        return os.path.normpath(clean_p)
        except Exception:
            pass

    # 2. Second priority: Analyze transcript tool paths
    paths: List[str] = []
    try:
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i > 250:
                    break
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                
                # Check tool calls
                for tc in d.get('tool_calls', []):
                    args = tc.get('args', {})
                    for v in args.values():
                        if isinstance(v, str):
                            paths.extend(extract_path_candidates(v))
                
                # Check content
                content = d.get('content') or ''
                if content:
                    paths.extend(extract_path_candidates(content))
    except Exception:
        pass

    proj_scores: Dict[str, int] = {}
    for p in paths:
        low = p.lower()
        if '.gemini' in low or 'temp' in low or 'windows' in low or 'appdata' in low:
            continue
        
        # Match Desktop/GitHub/<Org>/<Repo> or Desktop/GitHub/<Repo>
        m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Desktop\\GitHub\\[^\\]+\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Desktop\\GitHub\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Desktop\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Documents\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'([A-Za-z]:\\[^\\]+\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'((?:/Users|/home)/[^/]+/[^/]+)', p)
        
        if m:
            root = m.group(1).rstrip('\\')
            proj_scores[root] = proj_scores.get(root, 0) + 1

    if proj_scores:
        return max(proj_scores.items(), key=lambda x: x[1])[0]

    return default_fallback

def scan_conversations(brain_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scans the brain directory and returns structured metadata for all conversations,
    enriched with SQLite database titles and timestamps.
    """
    if brain_dir is None:
        brain_dir = get_brain_dir()

    if not os.path.exists(brain_dir):
        return []

    default_fallback = os.path.expanduser(os.path.join("~", "Desktop", "GitHub", "Public"))
    if not os.path.exists(default_fallback):
        default_fallback = os.path.expanduser("~")

    # Load SQLite metadata cache
    db_meta = load_conversation_db_metadata()

    results: List[Dict[str, Any]] = []

    for entry in os.listdir(brain_dir):
        conv_dir = os.path.join(brain_dir, entry)
        if not os.path.isdir(conv_dir):
            continue

        log_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
            continue

        first_prompt = ""
        first_time = 0
        turn_count = 0
        step_count = 0

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        step_count += 1
                        stype = d.get('type')
                        if stype == 'USER_INPUT':
                            turn_count += 1
                            if not first_prompt:
                                raw = d.get('content', '')
                                smart = extract_smart_title(raw)
                                if smart:
                                    first_prompt = smart
                        if not first_time and 'created_at' in d:
                            first_time = d.get('created_at')
                    except Exception:
                        continue
        except Exception:
            continue

        if step_count == 0:
            continue

        # Check SQLite db or overrides for clean title
        cid_meta = db_meta.get(entry, {})
        clean_title = (
            TITLE_OVERRIDES.get(entry) or
            cid_meta.get("title") or
            first_prompt or
            f"Antigravity Session {entry[:8]}"
        )

        db_workspace = cid_meta.get("workspace_uris", "")
        proj_dir = detect_project_dir(log_path, default_fallback, db_workspace)

        # Preserve genuine last_modified timestamp if present
        actual_time = first_time or cid_meta.get("last_modified")

        results.append({
            "id": entry,
            "dir": conv_dir,
            "transcript_path": log_path,
            "first_prompt": clean_title,
            "created_at": actual_time,
            "step_count": step_count,
            "turn_count": turn_count,
            "project_dir": proj_dir
        })

    # Sort descending by step count or date
    results.sort(key=lambda x: x["step_count"], reverse=True)
    return results
