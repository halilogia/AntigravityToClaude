"""
scanner.py - Scans Antigravity brain directories and discovers conversation trajectories.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

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
    """Strips internal XML tags and formatting noise from prompt content."""
    if not raw_text:
        return ""
    # Strip metadata blocks including their inner contents
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', raw_text, flags=re.DOTALL)
    text = re.sub(r'<CONTEXT_SUMMARY>.*?</CONTEXT_SUMMARY>', '', text, flags=re.DOTALL)
    text = re.sub(r'<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>', '', text, flags=re.DOTALL)
    # Strip USER_REQUEST tags but preserve the inner prompt text
    text = re.sub(r'</?USER_REQUEST[^>]*>', '', text)
    # Strip nested system context blocks if present
    text = re.sub(r'<user_information>.*?</user_information>', '', text, flags=re.DOTALL)
    text = re.sub(r'<conversation_transcript>.*?</conversation_transcript>', '', text, flags=re.DOTALL)
    text = re.sub(r'<skills>.*?</skills>', '', text, flags=re.DOTALL)
    text = re.sub(r'<guidelines>.*?</guidelines>', '', text, flags=re.DOTALL)
    text = text.strip()
    return text

def extract_smart_title(raw_text: str) -> str:
    """Extracts a clean, human-friendly title from a raw prompt."""
    cleaned = clean_prompt_text(raw_text)
    if not cleaned:
        return ""
    # Strip markdown artifacts
    t = re.sub(r'[*_`#~>]', ' ', cleaned)
    # Strip list numbering e.g. 1) 2) or 1. 2.
    t = re.sub(r'^\s*\d+[\.\)]\s*', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    # Find first meaningful sentence or clause
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

def detect_project_dir(transcript_path: str, default_fallback: str) -> str:
    """
    Analyzes tool calls, file paths, and environment hints in the transcript
    to find the true project/workspace root.
    """
    paths: List[str] = []
    try:
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i > 200:  # Scan up to 200 steps for performance
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
                            m = re.findall(r'[A-Za-z]:\\[^\s"\'<>:|?*]+', v)
                            paths.extend(m)
                
                # Check content
                content = d.get('content') or ''
                m = re.findall(r'[A-Za-z]:\\[^\s"\'<>:|?*]+', content)
                paths.extend(m)
    except Exception:
        pass

    proj_scores: Dict[str, int] = {}
    for p in paths:
        low = p.lower()
        if '.gemini' in low or 'temp' in low or 'windows' in low or 'appdata' in low:
            continue
        
        # Match Desktop/GitHub/<Org>/<Repo>
        m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Desktop\\GitHub\\[^\\]+\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Desktop\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            m = re.match(r'([A-Za-z]:\\Users\\[^\\]+\\Documents\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            # Match arbitrary drive project roots e.g. D:\dev\repo or C:\projects\repo
            m = re.match(r'([A-Za-z]:\\[^\\]+\\[^\\]+)', p, re.IGNORECASE)
        if not m:
            # Match macOS / Linux user directories
            m = re.match(r'((?:/Users|/home)/[^/]+/[^/]+)', p)
        
        if m:
            root = m.group(1).rstrip('\\')
            proj_scores[root] = proj_scores.get(root, 0) + 1

    if proj_scores:
        # Return path with highest score
        return max(proj_scores.items(), key=lambda x: x[1])[0]

    return default_fallback

def scan_conversations(brain_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scans the brain directory and returns structured metadata for all conversations.
    """
    if brain_dir is None:
        brain_dir = get_brain_dir()

    if not os.path.exists(brain_dir):
        return []

    default_fallback = os.path.expanduser(os.path.join("~", "Desktop", "GitHub", "Public"))
    if not os.path.exists(default_fallback):
        default_fallback = os.path.expanduser("~")

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
                                if 'created_at' in d:
                                    first_time = d.get('created_at')
                    except Exception:
                        continue
        except Exception:
            continue

        if step_count == 0:
            continue

        proj_dir = detect_project_dir(log_path, default_fallback)

        results.append({
            "id": entry,
            "dir": conv_dir,
            "transcript_path": log_path,
            "first_prompt": first_prompt or f"Antigravity Session {entry[:8]}",
            "created_at": first_time,
            "step_count": step_count,
            "turn_count": turn_count,
            "project_dir": proj_dir
        })

    # Sort descending by step count or date
    results.sort(key=lambda x: x["step_count"], reverse=True)
    return results
