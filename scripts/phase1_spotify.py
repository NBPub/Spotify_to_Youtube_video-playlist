"""
Phase 1: Fetch Spotify playlists and write per-playlist CSVs.

Usage:
    python scripts/phase1_spotify.py                      # interactive selection
    python scripts/phase1_spotify.py --playlist "Name"    # exact match or fuzzy select
    python scripts/phase1_spotify.py --all                # process all playlists
"""
import argparse
import os
import sys
from dotenv import load_dotenv
import spotipy
from utils.spotify_auth import get_spotify_client
from utils.csv_ops import get_csv_path, write_playlist_csv, read_playlist_csv
from utils.cli import select_playlist

load_dotenv()


def get_all_user_playlists(sp):
    """Return list of {id, name, tracks_href} dicts for all playlists in the user's library."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        for item in results["items"]:
            if item and item.get("id") and item.get("name"):
                playlists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "tracks_href": item.get("tracks", {}).get("href"),
                })
        results = sp.next(results) if results["next"] else None
    return playlists


def get_track_rows(sp, playlist_id, tracks_href=None):
    """Fetch all tracks from a playlist and return list of row dicts.

    Prefers tracks_href (Spotify's own canonical URL from the playlist listing)
    over constructing the /items URL manually. Exportify uses this same approach
    and successfully reads third-party playlists (e.g. Music League).
    The /tracks endpoint returns 'track' as the field name; /items returns 'item'.
    """
    track_items = []
    if tracks_href:
        results = sp._get(tracks_href)
    else:
        bare_id = playlist_id.split(":")[-1]
        results = sp._get(f"playlists/{bare_id}/items", additional_types="track")

    while results:
        track_items.extend(results["items"])
        results = sp.next(results) if results.get("next") else None

    rows = []
    for playlist_item in track_items:
        # /tracks endpoint uses "track"; /items endpoint uses "item"
        track = playlist_item.get("track") or playlist_item.get("item")
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


def process_playlist(sp_user, playlist):
    """Fetch tracks for one playlist using the user client and write to CSV."""
    name = playlist["name"]
    path = get_csv_path(name)
    existing = read_playlist_csv(path)
    if existing:
        print(f"  CSV already exists for '{name}' ({len(existing)} rows). Skipping.")
        return
    print(f"  Fetching tracks for '{name}'...")
    try:
        rows = get_track_rows(sp_user, playlist["id"], playlist.get("tracks_href"))
    except spotipy.exceptions.SpotifyException as e:
        print(f"  ERROR fetching '{name}': HTTP {e.http_status} — {e.msg}")
        if e.http_status == 403:
            print("  Hint: 403 Forbidden — playlist may be private or owned by a third party.")
            print("  Try adding the playlist to your Spotify profile and re-running.")
        return
    write_playlist_csv(path, rows)
    print(f"  Written {len(rows)} tracks to {path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Spotify playlists → CSVs")
    parser.add_argument("--playlist", help="Playlist name (exact match or interactive select)")
    parser.add_argument("--all", action="store_true", help="Process all user playlists")
    args = parser.parse_args()

    folder_label = os.getenv("PLAYLIST_FOLDER", "")
    print("Connecting to Spotify (user account)...")
    try:
        sp_user = get_spotify_client()
    except spotipy.exceptions.SpotifyException as e:
        print(f"ERROR: Spotify user authentication failed: HTTP {e.http_status} — {e.msg}")
        sys.exit(1)

    print("Fetching your playlists...")
    playlists = get_all_user_playlists(sp_user)
    playlist_names = [p["name"] for p in playlists]
    name_to_playlist = {p["name"]: p for p in playlists}

    if args.all:
        selected = playlists
    else:
        label = f"Your playlists (folder hint: {folder_label})" if folder_label else "Your playlists"
        print(label)
        chosen_names = select_playlist(playlist_names, args.playlist)
        selected = playlists if not chosen_names else [name_to_playlist[n] for n in chosen_names]

    for playlist in selected:
        process_playlist(sp_user, playlist)

    print("Phase 1 complete.")


if __name__ == "__main__":
    main()
