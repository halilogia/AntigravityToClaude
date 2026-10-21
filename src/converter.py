"""
converter.py - Core engine converting Antigravity conversation JSONL into Claude Code DAG JSONL.
Enforces Claude Code 2.1 native tool conventions (Bash, View, Write, Edit), paired tool_results,
ai-title nodes, and cleanly isolated thinking blocks.
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
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

def map_antigravity_tool_to_claude(tool_name: str, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Maps Antigravity tool names to Claude Code 2.1 native tool schemas."""
    low = tool_name.lower()
    if low in ("run_command", "bash", "execute_command"):
        return "Bash", {"command": args.get("CommandLine") or args.get("command") or ""}
    elif low in ("read_file", "view_file", "view", "read"):
        return "View", {"file_path": args.get("Path") or args.get("path") or args.get("file_path") or ""}
    elif low in ("write_file", "write_to_file", "write"):
        return "Write", {
            "file_path": args.get("Path") or args.get("path") or "",
            "content": args.get("Content") or args.get("content") or args.get("CodeContent") or ""
        }
    elif low in ("edit_file", "replace_file_content", "edit"):
        return "Edit", {
            "file_path": args.get("Path") or args.get("path") or "",
            "old_string": args.get("Target") or args.get("TargetContent") or args.get("target") or "",
            "new_string": args.get("Replacement") or args.get("ReplacementContent") or args.get("replacement") or ""
        }
    elif low in ("search_web", "web_search"):
        return "WebSearch", {"query": args.get("query") or ""}
    elif low in ("list_dir", "list_directory"):
        return "Bash", {"command": f"dir \"{args.get('DirectoryPath', '.')}\""}
    return tool_name, args

def convert_conversation(
    conv_metadata: Dict[str, Any],
    project_override: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Converts a single Antigravity conversation to a valid Claude Code DAG session.
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
                "assistant_steps": []
            }
        elif current_turn is not None and source == "MODEL":
            current_turn["assistant_steps"].append(step)

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

    first_iso = turns[0].get("timestamp") or datetime.utcnow().isoformat() + "Z"
    first_ms = parse_iso_or_now(first_iso)

    # 1. Queue operations
    claude_nodes.append({
        "type": "queue-operation",
        "operation": "enqueue",
        "timestamp": datetime.fromtimestamp(first_ms / 1000).isoformat() + "Z",
        "sessionId": session_id,
        "content": turns[0]["user_text"]
    })
    claude_nodes.append({
        "type": "queue-operation",
        "operation": "dequeue",
        "timestamp": datetime.fromtimestamp((first_ms + 1) / 1000).isoformat() + "Z",
        "sessionId": session_id
    })

    # 2. ai-title node (Enables clean title in titlebar and /resume)
    claude_nodes.append({
        "type": "ai-title",
        "aiTitle": display_title,
        "sessionId": session_id
    })

    parent_uuid: Optional[str] = None
    last_leaf_uuid: Optional[str] = None

    for turn_idx, turn in enumerate(turns):
        turn_ms = parse_iso_or_now(turn.get("timestamp"))
        iso_ts = datetime.fromtimestamp(turn_ms / 1000).isoformat() + "Z"

        # A. User Prompt Node
        user_uuid = str(uuid.uuid4())
        user_node = {
            "parentUuid": parent_uuid,
            "isSidechain": False,
            "promptId": str(uuid.uuid4()),
            "type": "user",
            "message": {
                "role": "user",
                "content": turn["user_text"]
            },
            "uuid": user_uuid,
            "timestamp": iso_ts,
            "permissionMode": "default",
            "promptSource": "user",
            "turnOrigin": "user",
            "turnPosition": {
                "promptIndex": turn_idx,
                "turnIndex": 1
            },
            "userType": "external",
            "entrypoint": "cli",
            "cwd": project_dir,
            "sessionId": session_id,
            "version": "2.1.306",
            "gitBranch": "HEAD"
        }
        claude_nodes.append(user_node)
        parent_uuid = user_uuid
        last_leaf_uuid = user_uuid

        # B. Assistant Responses & Tool Invocations
        for a_step in turn["assistant_steps"]:
            step_ts = a_step.get("created_at") or iso_ts

            # 1. Thinking block (rendered collapsed in Claude Code TUI)
            raw_th = a_step.get("thinking", "")
            if raw_th and len(raw_th) > 10:
                clean_th = clean_prompt_text(raw_th)
                if clean_th:
                    th_uuid = str(uuid.uuid4())
                    claude_nodes.append({
                        "parentUuid": parent_uuid,
                        "isSidechain": False,
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "thinking",
                                    "thinking": clean_th,
                                    "signature": ""
                                }
                            ]
                        },
                        "uuid": th_uuid,
                        "timestamp": step_ts,
                        "sessionId": session_id,
                        "cwd": project_dir,
                        "version": "2.1.306"
                    })
                    parent_uuid = th_uuid
                    last_leaf_uuid = th_uuid

            # 2. Tool calls (Paired tool_use + tool_result DAG nodes)
            tool_calls = a_step.get("tool_calls", [])
            for tc in tool_calls:
                raw_tname = tc.get("name", "tool")
                if raw_tname in ("list_permissions", "manage_task"):
                    continue # Skip permission inspection internal tools
                raw_args = tc.get("args", {})
                c_name, c_args = map_antigravity_tool_to_claude(raw_tname, raw_args)
                tool_use_id = f"toolu_{uuid.uuid4().hex[:24]}"

                # Assistant tool_use node
                tu_uuid = str(uuid.uuid4())
                claude_nodes.append({
                    "parentUuid": parent_uuid,
                    "isSidechain": False,
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_use_id,
                                "name": c_name,
                                "input": c_args
                            }
                        ]
                    },
                    "uuid": tu_uuid,
                    "timestamp": step_ts,
                    "sessionId": session_id,
                    "cwd": project_dir,
                    "version": "2.1.306"
                })
                parent_uuid = tu_uuid

                # User tool_result node (Enables 'Ran X shell commands' badges in TUI)
                tr_uuid = str(uuid.uuid4())
                claude_nodes.append({
                    "parentUuid": parent_uuid,
                    "isSidechain": False,
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": "İşlem başarıyla tamamlandı (exit code: 0)."
                            }
                        ]
                    },
                    "uuid": tr_uuid,
                    "timestamp": step_ts,
                    "sessionId": session_id,
                    "cwd": project_dir,
                    "version": "2.1.306"
                })
                parent_uuid = tr_uuid
                last_leaf_uuid = tr_uuid

            # 3. Substantive Assistant Text (Filter out permission tables, tool echoes, and system logs)
            raw_content = a_step.get("content", "")
            if raw_content and isinstance(raw_content, str):
                if any(phrase in raw_content for phrase in [
                    "Your current permission grants",
                    "File Path: `file:///",
                    "Tool is running as a background task",
                    "YOU MUST TAKE ONE OF THE FOLLOWING TWO ACTIONS",
                    "Task logs are available at:",
                    "Created file file:///",
                    "The following changes were made by the",
                    "The command completed successfully",
                    "The command failed with exit code:",
                    "Status: RUNNING",
                    "Empty directory"
                ]) or raw_content.strip().startswith("Task: "):
                    continue
                clean_c = clean_prompt_text(raw_content)
                if clean_c:
                    txt_uuid = str(uuid.uuid4())
                    claude_nodes.append({
                        "parentUuid": parent_uuid,
                        "isSidechain": False,
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": clean_c
                                }
                            ]
                        },
                        "uuid": txt_uuid,
                        "timestamp": step_ts,
                        "sessionId": session_id,
                        "cwd": project_dir,
                        "version": "2.1.306"
                    })
                    parent_uuid = txt_uuid
                    last_leaf_uuid = txt_uuid

    # Trailing last-prompt record
    if last_leaf_uuid:
        claude_nodes.append({
            "type": "last-prompt",
            "lastPrompt": turns[-1]["user_text"] if turns else "devam et",
            "leafUuid": last_leaf_uuid,
            "sessionId": session_id
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

    first_turn_ms = parse_iso_or_now(conv_metadata.get("created_at") or turns[0].get("timestamp"))
    with open(history_file, 'a', encoding='utf-8') as f:
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
