"""
Phase 2: Search YouTube for matching videos and update playlist CSVs.

Usage:
    python scripts/phase2_yt_search.py                      # interactive selection
    python scripts/phase2_yt_search.py --playlist "Name"    # exact match or fuzzy select
    python scripts/phase2_yt_search.py --all                # process all CSVs in data/playlists/

YouTube quota cost: 100 units per search. Default daily limit: 9000 units (~90 songs/run).
Resumable: rows with an existing 'Music Video Found' value are skipped.

Match strictness is controlled by the MATCH_STRICTNESS env var (low/medium/high, default: medium).
"""
import argparse
import os
from dotenv import load_dotenv
from utils.youtube_auth import get_youtube_client
from utils.csv_ops import get_csv_path, read_playlist_csv, write_playlist_csv
from utils.matching import is_match, core_title
from utils.rate_limit import QuotaTracker, QuotaExceededError
from utils.cli import select_playlist

load_dotenv()

SEARCH_COST = 100


def search_videos(youtube, song_name, artist):
    """Returns a list of (title, channel, url) tuples for the top 3 results, or []."""
    primary_artist = artist.split(";")[0].strip()
    query = f"{primary_artist} - {core_title(song_name)} Official"
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=3,
    ).execute()
    results = []
    for item in response.get("items", []):
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        video_id = item["id"]["videoId"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        results.append((title, channel, url))
    return results


def process_csv(youtube, csv_path, quota, strictness="medium"):
    rows = read_playlist_csv(csv_path)
    if not rows:
        print(f"  No rows found in {csv_path}. Skipping.")
        return
    unprocessed = [r for r in rows if not r.get("Music Video Found")]
    est = len(unprocessed) * SEARCH_COST
    if quota.remaining < est:
        raise QuotaExceededError(
            f"Need ~{est} units for this playlist, only {quota.remaining} remaining. "
            "Skipping to avoid partial run. Re-run tomorrow to continue."
        )
    changed = False
    for row in rows:
        if row.get("Music Video Found"):
            continue  # Already processed
        song = row["Song Name"]
        artist = row["Artist"]
        try:
            quota.charge(SEARCH_COST)
        except QuotaExceededError as e:
            print(f"\n⚠️  {e}")
            write_playlist_csv(csv_path, rows)
            raise
        candidates = search_videos(youtube, song, artist)
        match = next(
            (c for c in candidates if is_match(song, artist, c[0], c[1], strictness=strictness)),
            None,
        )
        if match is None:
            row["Music Video Found"] = "FALSE"
            row["YouTube URL"] = ""
            if candidates:
                title, channel, _ = candidates[0]
                print(f"  ✗ {artist} - {song}")
                print(f"      YouTube returned: \"{title}\" by {channel}")
        else:
            title, channel, url = match
            row["Music Video Found"] = "TRUE"
            row["YouTube URL"] = url
            print(f"  ✓ {artist} - {song}")
        changed = True
        quota.sleep(1.5)
    if changed:
        write_playlist_csv(csv_path, rows)
        print(f"  Updated {csv_path}")


def get_available_csv_names():
    playlists_dir = os.path.join("data", "playlists")
    if not os.path.exists(playlists_dir):
        return []
    return [f[:-4] for f in os.listdir(playlists_dir) if f.endswith(".csv")]


def main():
    parser = argparse.ArgumentParser(description="Phase 2: YouTube search → update CSVs")
    parser.add_argument("--playlist", help="Playlist name")
    parser.add_argument("--all", action="store_true", help="Process all CSVs")
    parser.add_argument("--daily-limit", type=int, default=9000,
                        help="YouTube quota units to use per run (default: 9000)")
    args = parser.parse_args()
    available = get_available_csv_names()
    if not available:
        print("No CSVs found in data/playlists/. Run phase1 first.")
        return
    if args.all:
        selected_names = available
    else:
        chosen = select_playlist(available, args.playlist)
        selected_names = available if not chosen else chosen
    strictness = os.getenv("MATCH_STRICTNESS", "medium").lower()
    if strictness not in ("low", "medium", "high"):
        print(f"Warning: unrecognised MATCH_STRICTNESS '{strictness}', defaulting to 'medium'.")
        strictness = "medium"
    print("Connecting to YouTube...")
    youtube = get_youtube_client()
    quota = QuotaTracker(daily_limit=args.daily_limit)
    if quota.used > 0:
        print(f"Quota state: {quota.used} units already used today, {quota.remaining} remaining.")
    print(f"Match strictness: {strictness}")
    for name in selected_names:
        print(f"\nProcessing: {name}")
        path = get_csv_path(name)
        try:
            process_csv(youtube, path, quota, strictness=strictness)
        except QuotaExceededError:
            print("Stopping early due to quota limit. Re-run tomorrow to continue.")
            break
    print(f"\nPhase 2 complete. Quota used: {quota.used}/{quota.daily_limit} units.")


if __name__ == "__main__":
    main()
