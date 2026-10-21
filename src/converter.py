"""
converter.py - Core engine converting Antigravity conversation JSONL into Claude Code DAG JSONL.
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from .scanner import clean_prompt_text, get_claude_dir

def slugify_project_path(path: str) -> str:
    r"""
    Converts a filesystem path to Claude Code's slug format:
    e.g. C:\Users\Halil Emre\Desktop\GitHub\Public\LifeOS
      -> C--Users-Halil-Emre-Desktop-GitHub-Public-LifeOS
    """
    norm = os.path.normpath(path)
    # Replace drive colon C: with C--
    if len(norm) > 1 and norm[1] == ':':
        norm = norm[0] + '--' + norm[2:]
    # Replace slashes, backslashes, and spaces with hyphens
    slug = norm.replace('\\', '-').replace('/', '-').replace(' ', '-')
    # Collapse multiple consecutive hyphens (except leading C--)
    parts = slug.split('--', 1)
    if len(parts) == 2:
        return parts[0] + '--' + '-'.join(p for p in parts[1].split('-') if p)
    return '-'.join(p for p in slug.split('-') if p)

def parse_iso_or_now(iso_str: Optional[str]) -> int:
    """Parses ISO timestamp string to epoch milliseconds, fallback to current time."""
    if not iso_str:
        return int(time.time() * 1000)
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except Exception:
        return int(time.time() * 1000)

def convert_conversation(
    conv_metadata: Dict[str, Any],
    project_override: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Converts a single Antigravity conversation to a Claude Code session.
    Returns conversion report summary.
    """
    transcript_path = conv_metadata["transcript_path"]
    session_id = conv_metadata["id"]
    project_dir = project_override or conv_metadata.get("project_dir") or os.path.expanduser("~")
    display_title = conv_metadata.get("first_prompt") or f"Antigravity Session {session_id[:8]}"

    claude_dir = get_claude_dir()
    slug = slugify_project_path(project_dir)
    project_store_dir = os.path.join(claude_dir, "projects", slug)
    os.makedirs(project_store_dir, exist_ok=True)

    target_jsonl = os.path.join(project_store_dir, f"{session_id}.jsonl")
    if os.path.exists(target_jsonl) and not force:
        return {
            "status": "skipped",
            "session_id": session_id,
            "project_dir": project_dir,
            "reason": "already_exists",
            "file": target_jsonl
        }

    # Group transcript into sequential turns
    steps: List[Dict[str, Any]] = []
    try:
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    steps.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:
        return {
            "status": "error",
            "session_id": session_id,
            "error": str(e)
        }

    turns: List[Dict[str, Any]] = []
    current_turn: Optional[Dict[str, Any]] = None

    for step in steps:
        stype = step.get("type")
        source = step.get("source")

        if stype == "USER_INPUT" and source == "USER_EXPLICIT":
            if current_turn:
                turns.append(current_turn)
            raw_text = step.get("content", "")
            cleaned = clean_prompt_text(raw_text)
            current_turn = {
                "user_text": cleaned or "Devam et",
                "timestamp": step.get("created_at"),
                "assistant_responses": []
            }
        elif current_turn is not None and stype in ("PLANNER_RESPONSE", "GENERIC"):
            current_turn["assistant_responses"].append(step)

    if current_turn:
        turns.append(current_turn)

    if not turns:
        return {
            "status": "skipped",
            "session_id": session_id,
            "reason": "empty_turns"
        }

    # Build Claude Code DAG nodes
    claude_nodes: List[Dict[str, Any]] = []
    parent_uuid: Optional[str] = None
    last_assistant_uuid: Optional[str] = None

    for turn_idx, turn in enumerate(turns):
        turn_ms = parse_iso_or_now(turn.get("timestamp"))

        # 1. User Message
        user_uuid = str(uuid.uuid4())
        user_node = {
            "parentUuid": parent_uuid,
            "uuid": user_uuid,
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": turn["user_text"]
                    }
                ]
            },
            "timestamp": turn_ms
        }
        claude_nodes.append(user_node)
        parent_uuid = user_uuid

        # 2. Assistant Message
        assistant_uuid = str(uuid.uuid4())
        content_blocks: List[Dict[str, Any]] = []

        for resp in turn["assistant_responses"]:
            # Thinking / text
            thinking = resp.get("thinking")
            if thinking:
                content_blocks.append({
                    "type": "text",
                    "text": f"*(Düşünce Zinciri)*\n{thinking.strip()}\n"
                })

            txt = resp.get("content")
            if txt and isinstance(txt, str):
                txt_clean = clean_prompt_text(txt)
                if txt_clean:
                    content_blocks.append({
                        "type": "text",
                        "text": txt_clean
                    })

            # Tool calls
            for tc in resp.get("tool_calls", []):
                t_name = tc.get("name", "tool")
                t_args = tc.get("args", {})
                content_blocks.append({
                    "type": "tool_use",
                    "id": f"toolu_{uuid.uuid4().hex[:12]}",
                    "name": t_name,
                    "input": t_args
                })

        if not content_blocks:
            content_blocks.append({
                "type": "text",
                "text": "İşlem başarıyla tamamlandı."
            })

        assistant_node = {
            "parentUuid": parent_uuid,
            "uuid": assistant_uuid,
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": content_blocks
            },
            "timestamp": turn_ms + 1000
        }
        claude_nodes.append(assistant_node)
        parent_uuid = assistant_uuid
        last_assistant_uuid = assistant_uuid

    # Trailing last-prompt record
    if last_assistant_uuid:
        claude_nodes.append({
            "type": "last-prompt",
            "leafUuid": last_assistant_uuid
        })

    # Write project session JSONL
    with open(target_jsonl, 'w', encoding='utf-8') as f:
        for node in claude_nodes:
            f.write(json.dumps(node, ensure_ascii=False) + '\n')

    # Register in history.jsonl
    history_file = os.path.join(claude_dir, "history.jsonl")
    existing_entries = set()
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        h = json.loads(line)
                        if "sessionId" in h and "project" in h:
                            existing_entries.add((h["sessionId"], h["project"]))
                    except Exception:
                        continue
        except Exception:
            pass

    first_turn_ms = parse_iso_or_now(turns[0].get("timestamp")) if turns else int(time.time() * 1000)
    with open(history_file, 'a', encoding='utf-8') as f:
        # Register for detected project
        if (session_id, project_dir) not in existing_entries:
            history_entry = {
                "display": f"{display_title} (Antigravity)",
                "pastedContents": {},
                "timestamp": first_turn_ms,
                "project": project_dir,
                "sessionId": session_id
            }
            f.write(json.dumps(history_entry, ensure_ascii=False) + '\n')
            existing_entries.add((session_id, project_dir))

    return {
        "status": "converted",
        "session_id": session_id,
        "project_dir": project_dir,
        "turns_count": len(turns),
        "nodes_count": len(claude_nodes),
        "target_file": target_jsonl
    }
