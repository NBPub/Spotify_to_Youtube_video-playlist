"""
Phase 3: Create Unlisted YouTube playlists from playlist CSVs.

Usage:
    python scripts/phase3_yt_playlist.py                      # interactive selection
    python scripts/phase3_yt_playlist.py --playlist "Name"
    python scripts/phase3_yt_playlist.py --all

YouTube quota cost:
  - Create playlist: 50 units
  - Add video: 50 units per video
Default daily limit: 9000 units.
Resumable: rows with 'Added to YT Playlist' = TRUE are skipped.
Playlist URLs are written automatically to data/summary.csv after each successful run.
"""
import argparse
import os
import time
from googleapiclient.errors import HttpError
from utils.youtube_auth import get_youtube_client
from utils.csv_ops import (
    get_csv_path,
    read_playlist_csv,
    write_playlist_csv,
    upsert_summary,
    lookup_summary_url,
)
from utils.rate_limit import QuotaTracker, QuotaExceededError
from utils.cli import select_playlist

TRANSIENT_STATUS_CODES = {409, 500, 503}

CREATE_PLAYLIST_COST = 50
ADD_VIDEO_COST = 50


def create_youtube_playlist(youtube, name):
    response = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": name,
                "description": f"Spotify playlist: {name}",
            },
            "status": {"privacyStatus": "unlisted"},
        },
    ).execute()
    playlist_id = response["id"]
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    return playlist_id, url


def add_video_to_playlist(youtube, playlist_id, video_url, max_retries=3):
    video_id = video_url.split("v=")[-1]
    for attempt in range(max_retries):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            return
        except HttpError as e:
            if e.status_code in TRANSIENT_STATUS_CODES and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Transient error ({e.status_code}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def get_or_create_playlist(youtube, name, rows, quota, resume_playlist_id=None):
    already_added = [r for r in rows if r.get("Added to YT Playlist") == "TRUE"]
    if already_added:
        if not resume_playlist_id:
            print(f"  {len(already_added)} songs already marked as added. "
                  "Pass --resume-playlist-id <id> to continue adding to the existing playlist.")
            return None, None
        url = f"https://www.youtube.com/playlist?list={resume_playlist_id}"
        print(f"  Resuming into existing playlist: {url} ({len(already_added)} songs already added)")
        return resume_playlist_id, url
    quota.charge(CREATE_PLAYLIST_COST)
    playlist_id, url = create_youtube_playlist(youtube, name)
    print(f"  Created playlist: {url}")
    quota.sleep(1.5)
    return playlist_id, url


def process_csv(youtube, name, quota, resume_playlist_id=None):
    path = get_csv_path(name)
    rows = read_playlist_csv(path)
    if not rows:
        print(f"  No rows in {path}. Skipping.")
        return None
    eligible = [r for r in rows if r.get("Music Video Found") == "TRUE"]
    if not eligible:
        print(f"  No videos found for '{name}'. Skipping playlist creation.")
        return None
    already_added = [r for r in rows if r.get("Added to YT Playlist") == "TRUE"]
    if not already_added:
        est = CREATE_PLAYLIST_COST + len(eligible) * ADD_VIDEO_COST
        if quota.remaining < est:
            raise QuotaExceededError(
                f"Need ~{est} units for '{name}', only {quota.remaining} remaining. "
                "Skipping to avoid partial playlist. Re-run tomorrow."
            )
    playlist_id, playlist_url = get_or_create_playlist(
        youtube, name, rows, quota, resume_playlist_id
    )
    if not playlist_id:
        # Refresh summary from current CSV state so phase 4 doesn't show stale
        # counts after phase 2 finds new matches but phase 3 can't add them
        # (e.g. already-added rows present and no --resume-playlist-id given).
        existing_url = lookup_summary_url(name)
        if existing_url:
            videos = sum(1 for r in rows if r.get("Added to YT Playlist") == "TRUE")
            upsert_summary(name, len(rows), videos, existing_url)
        return None
    for row in rows:
        if row.get("Music Video Found") != "TRUE":
            continue
        if row.get("Added to YT Playlist") == "TRUE":
            continue
        try:
            quota.charge(ADD_VIDEO_COST)
        except QuotaExceededError as e:
            print(f"\n⚠️  {e}")
            write_playlist_csv(path, rows)
            raise
        try:
            add_video_to_playlist(youtube, playlist_id, row["YouTube URL"])
        except HttpError as e:
            print(f"\n  ERROR adding '{row['Song Name']}': {e}")
            write_playlist_csv(path, rows)
            raise
        row["Added to YT Playlist"] = "TRUE"
        print(f"  Added: {row['Artist']} - {row['Song Name']}")
        quota.sleep(1.5)
    write_playlist_csv(path, rows)
    tracks = len(rows)
    videos = sum(1 for r in rows if r.get("Added to YT Playlist") == "TRUE")
    upsert_summary(name, tracks, videos, playlist_url)
    return playlist_url


def get_available_csv_names():
    playlists_dir = os.path.join("data", "playlists")
    if not os.path.exists(playlists_dir):
        return []
    return [f[:-4] for f in os.listdir(playlists_dir) if f.endswith(".csv")]


def main():
    parser = argparse.ArgumentParser(description="Phase 3: Create YouTube playlists")
    parser.add_argument("--playlist", help="Playlist name")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--daily-limit", type=int, default=9000)
    parser.add_argument("--resume-playlist-id", help="YouTube playlist ID to resume adding videos into")
    args = parser.parse_args()
    available = get_available_csv_names()
    if not available:
        print("No CSVs found in data/playlists/. Run phases 1 and 2 first.")
        return
    if args.all:
        selected_names = available
    else:
        chosen = select_playlist(available, args.playlist)
        selected_names = available if not chosen else chosen
    print("Connecting to YouTube...")
    youtube = get_youtube_client()
    quota = QuotaTracker(daily_limit=args.daily_limit)
    if quota.used > 0:
        print(f"Quota state: {quota.used} units already used today, {quota.remaining} remaining.")
    created = {}
    for name in selected_names:
        print(f"\nProcessing: {name}")
        try:
            url = process_csv(youtube, name, quota, args.resume_playlist_id)
            if url:
                created[name] = url
        except QuotaExceededError:
            print("Stopping early due to quota. Re-run tomorrow.")
            break
    print(f"\nPhase 3 complete. Quota used: {quota.used}/{quota.daily_limit} units.")
    if created:
        print("\nCreated playlists:")
        for name, url in created.items():
            print(f"  {name}: {url}")
        print("\nRun phase4_summary.py to view the full summary.")


if __name__ == "__main__":
    main()
