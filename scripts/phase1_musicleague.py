"""
Phase 1 (Music League): Fetch rounds from a Music League league → per-round CSVs.

Each round in the league maps to one CSV (and eventually one YouTube playlist).
Track metadata is fetched from Spotify's /tracks endpoint using app credentials —
no playlist ownership required, bypassing the 403 issue with third-party playlists.

Required env vars:
    MUSICLEAGUE_SESSION    — session cookie from browser (see utils/musicleague_client.py)
    MUSICLEAGUE_LEAGUE_ID  — league ID from the URL (falls back to hard-coded default)
    SPOTIFY_CLIENT_ID      — Spotify app credentials
    SPOTIFY_CLIENT_SECRET  — Spotify app credentials

Usage:
    python scripts/phase1_musicleague.py              # interactive round selection
    python scripts/phase1_musicleague.py --all        # all rounds
    python scripts/phase1_musicleague.py --round "Round Name"
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from utils.musicleague_client import get_ml_client
from utils.spotify_auth import get_spotify_app_client
from utils.csv_ops import get_csv_path, write_playlist_csv, read_playlist_csv
from utils.cli import select_playlist

load_dotenv()

LEAGUE_ID = os.getenv("MUSICLEAGUE_LEAGUE_ID", "83c15155b80143f2b678dc2e62011bda")
SPOTIFY_BATCH_SIZE = 50


def extract_track_id(uri: str) -> str:
    """Extract bare Spotify track ID from URI or URL."""
    if uri.startswith("spotify:track:"):
        return uri.split(":")[-1]
    if "open.spotify.com/track/" in uri:
        return uri.split("/track/")[-1].split("?")[0]
    return uri


def fetch_track_metadata(sp, track_ids: list[str]) -> dict[str, dict]:
    """Batch-fetch track metadata from Spotify. Returns {track_id: track_obj}."""
    metadata = {}
    for i in range(0, len(track_ids), SPOTIFY_BATCH_SIZE):
        batch = track_ids[i:i + SPOTIFY_BATCH_SIZE]
        results = sp.tracks(batch)
        for track in results.get("tracks", []):
            if track:
                metadata[track["id"]] = track
    return metadata


def get_round_rows(ml_client, sp, league_id: str, round_id: str, round_name: str) -> list[dict]:
    """Fetch submissions for one round and return CSV row dicts."""
    submissions = ml_client.get_round_results(league_id, round_id)
    if not submissions:
        print(f"  No submissions returned for '{round_name}'.")
        return []

    # Extract Spotify track IDs — try common field names for the URI
    track_ids = []
    for sub in submissions:
        uri = (
            sub.get("spotifyUri")
            or sub.get("uri")
            or sub.get("spotify_uri")
            or (sub.get("track") or {}).get("uri", "")
        )
        if uri:
            track_ids.append(extract_track_id(uri))

    if not track_ids:
        sample_keys = list(submissions[0].keys()) if submissions else []
        print(f"  WARNING: No Spotify URIs found in submissions.")
        print(f"  Submission fields available: {sample_keys}")
        print("  Check utils/musicleague_client.py to map the correct field name.")
        return []

    metadata = fetch_track_metadata(sp, track_ids)

    rows = []
    for track_id in track_ids:
        track = metadata.get(track_id)
        if not track:
            continue
        release_date = track["album"].get("release_date", "")
        release_year = release_date[:4] if release_date else ""
        rows.append({
            "Song Name": track["name"],
            "Artist": track["artists"][0]["name"] if track["artists"] else "",
            "Release Year": release_year,
            "Music Video Found": "",
            "Added to YT Playlist": "",
            "YouTube URL": "",
        })
    return rows


def round_name(r: dict) -> str:
    return r.get("name") or r.get("title") or r.get("id", "unknown")


def process_round(ml_client, sp, league_id: str, r: dict):
    name = round_name(r)
    round_id = r.get("id") or r.get("roundId", "")

    path = get_csv_path(name)
    existing = read_playlist_csv(path)
    if existing:
        print(f"  CSV already exists for '{name}' ({len(existing)} rows). Skipping.")
        return

    print(f"  Fetching tracks for round '{name}'...")
    rows = get_round_rows(ml_client, sp, league_id, round_id, name)
    if not rows:
        print(f"  No tracks written for '{name}'.")
        return

    write_playlist_csv(path, rows)
    print(f"  Written {len(rows)} tracks to {path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 1 (Music League): rounds → CSVs")
    parser.add_argument("--round", dest="round_name", help="Round name to process")
    parser.add_argument("--all", action="store_true", help="Process all rounds")
    parser.add_argument("--debug", action="store_true",
                        help="Probe the API step by step and print raw responses (for debugging)")
    args = parser.parse_args()

    print("Connecting to Music League...")
    try:
        ml = get_ml_client()
    except EnvironmentError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.debug:
        print("\n--- DEBUG: probing Music League API ---")
        print("\n[1] GET /me  (discover user ID)")
        try:
            me = ml.get_me(debug=True)
            user_id = me.get("id") or me.get("userId") or me.get("user_id")
            print(f"    User ID: {user_id}")
        except Exception as e:
            print(f"    Failed: {e}")
            user_id = None

        if user_id:
            print(f"\n[2] GET /users/{user_id}/leagues")
            try:
                leagues = ml.get_user_leagues(user_id, debug=True)
                print(f"    Found {len(leagues)} league(s)")
                for lg in leagues:
                    print(f"    - id={lg.get('id')} name={lg.get('name') or lg.get('title')}")
            except Exception as e:
                print(f"    Failed: {e}")

        print(f"\n[3] GET /leagues/{LEAGUE_ID}  (direct by URL ID)")
        try:
            ml.get_league(LEAGUE_ID, debug=True)
        except Exception as e:
            print(f"    Failed: {e}")

        print(f"\n[4] GET /leagues/{LEAGUE_ID}/rounds")
        try:
            ml.get_rounds(LEAGUE_ID, debug=True)
        except Exception as e:
            print(f"    Failed: {e}")

        print("\n--- end debug ---")
        sys.exit(0)

    print("Connecting to Spotify (app credentials for track metadata)...")
    try:
        sp = get_spotify_app_client()
    except EnvironmentError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Fetching rounds for league {LEAGUE_ID}...")
    try:
        rounds = ml.get_rounds(LEAGUE_ID)
    except PermissionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not rounds:
        print("No rounds returned. Run with --debug to probe the API and find the correct paths.")
        sys.exit(1)

    names = [round_name(r) for r in rounds]
    name_to_round = {round_name(r): r for r in rounds}
    print(f"Found {len(rounds)} round(s): {', '.join(names)}")

    if args.all:
        selected = rounds
    else:
        chosen_names = select_playlist(names, args.round_name)
        selected = rounds if not chosen_names else [name_to_round[n] for n in chosen_names]

    for r in selected:
        process_round(ml, sp, LEAGUE_ID, r)

    print("Phase 1 (Music League) complete.")


if __name__ == "__main__":
    main()
