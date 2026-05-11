"""
Run the full pipeline in sequence for selected playlists.

Phases:
  1. Import Exportify CSV → pipeline CSV
  2. Search YouTube for music videos → update CSV
  3. Create Unlisted YouTube playlist → update CSV + summary
  4. Summary CSV is updated automatically by phase 3

Only playlists not yet imported (no file in data/playlists/) are shown for selection.

Quota assumption: assumes a fresh daily YouTube quota at the start of each run
(default 9,000 units). If you ran any phase script manually earlier the same day,
those units are not tracked here — plan accordingly.

Usage:
    python scripts/run_pipeline.py                    # interactive selection
    python scripts/run_pipeline.py --all              # all new Exportify playlists
    python scripts/run_pipeline.py --daily-limit 5000
"""
import argparse
import os
import sys

from dotenv import load_dotenv
from utils.youtube_auth import get_youtube_client
from utils.rate_limit import QuotaTracker, QuotaExceededError
from utils.cli import select_playlist
from utils.csv_ops import get_csv_path

load_dotenv()
from scripts.phase1_exportify import get_available_playlists, process_playlist as phase1_process
from scripts.phase2_yt_search import process_csv as phase2_process
from scripts.phase3_yt_playlist import process_csv as phase3_process


def main():
    parser = argparse.ArgumentParser(description="Full pipeline: Exportify → YouTube")
    parser.add_argument("--all", action="store_true", help="Process all new Exportify playlists")
    parser.add_argument("--daily-limit", type=int, default=9000,
                        help="YouTube quota units budget for this run (default: 9000)")
    args = parser.parse_args()

    available = get_available_playlists()
    if not available:
        print("No new playlists found in 'exported playlists/'.")
        print("All playlists may already be imported, or the directory is empty.")
        return

    names = [p["name"] for p in available]
    name_to_entry = {p["name"]: p for p in available}

    if args.all:
        selected = available
    else:
        chosen_names = select_playlist(names)
        selected = available if not chosen_names else [name_to_entry[n] for n in chosen_names]

    strictness = os.getenv("MATCH_STRICTNESS", "medium").lower()
    if strictness not in ("low", "medium", "high"):
        print(f"Warning: unrecognised MATCH_STRICTNESS '{strictness}', defaulting to 'medium'.")
        strictness = "medium"

    print("\nConnecting to YouTube...")
    youtube = get_youtube_client()
    quota = QuotaTracker(daily_limit=args.daily_limit)
    if quota.used > 0:
        print(f"Quota state: {quota.used} units already used today, {quota.remaining} remaining.")
    print(f"Quota budget: {quota.daily_limit} units (~{quota.daily_limit // 100} searches or "
          f"~{quota.daily_limit // 50} playlist operations)")
    print(f"Match strictness: {strictness}")

    completed = []
    skipped_quota = []

    for i, entry in enumerate(selected):
        name = entry["name"]
        print(f"\n{'=' * 55}")
        print(f"  {name}  ({i + 1}/{len(selected)})")
        print(f"{'=' * 55}")

        # Phase 1: import Exportify CSV → pipeline CSV
        print("\n[Phase 1] Importing from Exportify...")
        phase1_process(entry)

        # Phase 2: YouTube search
        print("\n[Phase 2] Searching YouTube for matching videos...")
        try:
            phase2_process(youtube, get_csv_path(name), quota, strictness=strictness)
        except QuotaExceededError as e:
            print(f"\n  Quota limit reached: {e}")
            skipped_quota.extend(p["name"] for p in selected[i:])
            break

        # Phase 3: Create YouTube playlist
        print("\n[Phase 3] Creating YouTube playlist...")
        try:
            phase3_process(youtube, name, quota)
        except QuotaExceededError as e:
            print(f"\n  Quota limit reached: {e}")
            skipped_quota.extend(p["name"] for p in selected[i:])
            break

        completed.append(name)

    print(f"\n{'=' * 55}")
    print("Pipeline run complete.")
    print(f"Quota used: {quota.used}/{quota.daily_limit} units ({quota.remaining} remaining)")
    if completed:
        print(f"\nCompleted ({len(completed)}): {', '.join(completed)}")
    if skipped_quota:
        print(f"\nNot started — quota: {', '.join(skipped_quota)}")
        print("Re-run tomorrow to continue.")


if __name__ == "__main__":
    main()
