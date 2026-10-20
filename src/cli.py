"""
cli.py - Interactive CLI interface and single-click runner for AntigravityToClaude.
"""

import os
import sys
import argparse
from typing import List, Dict, Any

# Safe UTF-8 reconfiguration on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from .scanner import scan_conversations, get_brain_dir, get_claude_dir
from .converter import convert_conversation

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BANNER = f"""{CYAN}{BOLD}
+==============================================================================+
|                  ANTIGRAVITY -> CLAUDE CODE MIGRATOR                         |
|            Tek Tikla Tum Antigravity Sohbetlerini Claude'a Aktar             |
|                                v1.0.0                                        |
+==============================================================================+{RESET}
"""

def print_banner():
    # Enable ANSI escape sequences on Windows if needed
    if os.name == 'nt':
        os.system('')
    print(BANNER)

def run_migration(
    conversations: List[Dict[str, Any]],
    force: bool = False,
    dry_run: bool = False,
    project_override: str = None
):
    total = len(conversations)
    print(f"{YELLOW}▶ Toplam {BOLD}{total}{RESET}{YELLOW} geçerli Antigravity sohbeti tespit edildi.{RESET}\n")

    converted_count = 0
    skipped_count = 0
    error_count = 0

    print(f"{'DURUM':<12} | {'OTURUM ID':<38} | {'TUR':<5} | {'BAŞLIK'}")
    print("-" * 90)

    for idx, c in enumerate(conversations, start=1):
        c_id = c["id"]
        title = (c["first_prompt"] or "İsimsiz Oturum")[:35]
        turns = c["turn_count"]

        if dry_run:
            print(f"{CYAN}[DRY-RUN]{RESET}    | {c_id:<38} | {turns:<5} | {title}")
            continue

        res = convert_conversation(c, project_override=project_override, force=force)
        status = res.get("status")

        if status == "converted":
            converted_count += 1
            print(f"{GREEN}[AKT python]{RESET}   | {c_id:<38} | {turns:<5} | {title}")
        elif status == "skipped":
            skipped_count += 1
            reason = res.get("reason", "mevcut")
            print(f"{DIM}[MEVCUT]{RESET}    | {c_id:<38} | {turns:<5} | {title} {DIM}({reason}){RESET}")
        else:
            error_count += 1
            err = res.get("error", "Bilinmeyen hata")[:20]
            print(f"{RED}[HATA]{RESET}      | {c_id:<38} | {turns:<5} | {title} {RED}({err}){RESET}")

    print("\n" + "=" * 90)
    print(f"{BOLD}📊 AKTARIM ÖZETİ:{RESET}")
    print(f"  • Yeni Aktarılan : {GREEN}{BOLD}{converted_count}{RESET}")
    print(f"  • Zaten Mevcut   : {DIM}{skipped_count}{RESET}")
    print(f"  • Hata           : {RED}{error_count}{RESET}")
    print(f"  • Toplam Taranan : {total}")
    print("=" * 90)

    claude_dir = get_claude_dir()
    print(f"\n{CYAN}💡 Claude Code Oturumlarını Başlatmak İçin:{RESET}")
    print(f"  1) Claude interaktif seçiciyi açmak için:  {BOLD}claude --resume{RESET}")
    print(f"  2) Belirli bir oturumu doğrudan açmak için: {BOLD}claude --resume <OTURUM_ID>{RESET}\n")

def list_conversations(conversations: List[Dict[str, Any]]):
    print(f"{'#':<3} | {'OTURUM ID':<38} | {'ADIM':<5} | {'TUR':<4} | {'PROJE / HEDEF':<30} | {'İLK MESAJ'}")
    print("-" * 120)
    for idx, c in enumerate(conversations, start=1):
        c_id = c["id"]
        steps = c["step_count"]
        turns = c["turn_count"]
        proj = os.path.basename(c["project_dir"]) or c["project_dir"]
        title = (c["first_prompt"] or "İsimsiz")[:35]
        print(f"{idx:<3} | {c_id:<38} | {steps:<5} | {turns:<4} | {proj:<30} | {title}")

def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Antigravity to Claude Code Conversation Migrator"
    )
    parser.add_argument("--all", action="store_true", help="Tüm Antigravity sohbetlerini otomatik aktar")
    parser.add_argument("--list", action="store_true", help="Tespit edilen Antigravity sohbetlerini listele")
    parser.add_argument("--id", type=str, help="Yalnızca belirtilen oturum ID'sini aktar")
    parser.add_argument("--project", type=str, help="Oturumlar için özel hedef proje klasörü belirt")
    parser.add_argument("--force", action="store_true", help="Önceden aktarılmış oturumların üzerine yaz")
    parser.add_argument("--dry-run", action="store_true", help="Dosya yazmadan simülasyon yap")
    parser.add_argument("--brain-dir", type=str, help="Özel Antigravity brain klasörü yolu")

    args = parser.parse_args()

    brain_dir = args.brain_dir or get_brain_dir()
    if not os.path.exists(brain_dir):
        print(f"{RED}[HATA] Antigravity brain klasörü bulunamadı: {brain_dir}{RESET}")
        sys.exit(1)

    print(f"{DIM}📂 Taranan Antigravity Dizini: {brain_dir}{RESET}")
    conversations = scan_conversations(brain_dir)

    if not conversations:
        print(f"{YELLOW}Uyarı: Belirtilen dizinde geçerli Antigravity sohbeti bulunamadı.{RESET}")
        sys.exit(0)

    if args.list:
        list_conversations(conversations)
        return

    if args.id:
        target = [c for c in conversations if c["id"].lower() == args.id.lower()]
        if not target:
            print(f"{RED}[HATA] '{args.id}' ID'li sohbet bulunamadı!{RESET}")
            sys.exit(1)
        run_migration(target, force=args.force, dry_run=args.dry_run, project_override=args.project)
        return

    # Default action: run all migrations (single-click friendly!)
    run_migration(conversations, force=args.force, dry_run=args.dry_run, project_override=args.project)

    # If running interactively / double-clicked on Windows, pause before exit
    if sys.stdin.isatty():
        try:
            input(f"\n{GREEN}✔ Tüm işlemler tamamlandı. Çıkmak için Enter'a basın...{RESET}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
