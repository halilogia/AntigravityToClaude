"""
Unit tests for AntigravityToClaude
"""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scanner import clean_prompt_text
from src.converter import slugify_project_path, convert_conversation

class TestAntigravityToClaude(unittest.TestCase):
    def test_slugify(self):
        p1 = r"C:\Users\Halil Emre\Desktop\GitHub\Public\LifeOS"
        s1 = slugify_project_path(p1)
        self.assertTrue(s1.startswith("C--Users-Halil-Emre"))
        self.assertNotIn(":", s1)
        self.assertNotIn("\\", s1)
        self.assertNotIn(" ", s1)

    def test_clean_prompt_text(self):
        raw = "<USER_REQUEST>\nTamam bunu yap\n</USER_REQUEST><ADDITIONAL_METADATA>\ntime: 123\n</ADDITIONAL_METADATA>"
        cleaned = clean_prompt_text(raw)
        self.assertEqual(cleaned, "Tamam bunu yap")

    def test_convert_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock transcript
            log_dir = os.path.join(tmpdir, ".system_generated", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "transcript.jsonl")

            steps = [
                {
                    "step_index": 0,
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "created_at": "2026-10-20T12:00:00Z",
                    "content": "<USER_REQUEST>Merhaba Dünya</USER_REQUEST>"
                },
                {
                    "step_index": 1,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-10-20T12:00:02Z",
                    "thinking": "Düşünüyorum...",
                    "content": "Sana da merhaba!",
                    "tool_calls": []
                }
            ]

            with open(log_file, 'w', encoding='utf-8') as f:
                for s in steps:
                    f.write(json.dumps(s) + "\n")

            mock_meta = {
                "id": "mock-session-1234",
                "dir": tmpdir,
                "transcript_path": log_file,
                "first_prompt": "Merhaba Dünya",
                "created_at": "2026-10-20T12:00:00Z",
                "step_count": 2,
                "turn_count": 1,
                "project_dir": tmpdir
            }

            # Set custom CLAUDE_DIR to tmpdir
            os.environ["CLAUDE_DIR"] = os.path.join(tmpdir, ".claude")

            res = convert_conversation(mock_meta, force=True)
            self.assertEqual(res["status"], "converted")
            self.assertEqual(res["turns_count"], 1)

            target_file = res["target_file"]
            self.assertTrue(os.path.exists(target_file))

            # Inspect nodes
            nodes = []
            with open(target_file, 'r', encoding='utf-8') as f:
                for l in f:
                    nodes.append(json.loads(l))

            # user, assistant, last-prompt
            self.assertEqual(len(nodes), 3)
            self.assertEqual(nodes[0]["type"], "user")
            self.assertIsNone(nodes[0]["parentUuid"])

            self.assertEqual(nodes[1]["type"], "assistant")
            self.assertEqual(nodes[1]["parentUuid"], nodes[0]["uuid"])

            self.assertEqual(nodes[2]["type"], "last-prompt")
            self.assertEqual(nodes[2]["leafUuid"], nodes[1]["uuid"])

if __name__ == "__main__":
    unittest.main()
