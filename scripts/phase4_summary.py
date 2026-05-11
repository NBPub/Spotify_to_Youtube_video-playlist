"""
Phase 4: Display data/summary.csv — the master list of Spotify playlists and their YouTube URLs.

The summary CSV is written automatically by phase3_yt_playlist.py after each playlist is created.
Run this script at any time to see the current state.

Usage:
    python scripts/phase4_summary.py
"""
import os
from utils.csv_ops import SUMMARY_FILE, read_playlist_csv


def main():
    if not os.path.exists(SUMMARY_FILE):
        print(f"No summary file found at {SUMMARY_FILE}.")
        print("Run phase3_yt_playlist.py to create playlists — the summary is written automatically.")
        return
    rows = read_playlist_csv(SUMMARY_FILE)
    if not rows:
        print(f"{SUMMARY_FILE} is empty.")
        return
    print(f"Summary — {len(rows)} playlist(s):\n")
    for row in rows:
        print(f"  {row['Playlist Name']}")
        print(f"    {row['YouTube Playlist URL']}")


if __name__ == "__main__":
    main()
