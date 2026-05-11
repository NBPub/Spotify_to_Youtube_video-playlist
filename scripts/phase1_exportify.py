"""
Phase 1 (Exportify): Import Exportify playlist CSVs → pipeline CSVs.

Reads exported CSVs from 'exported playlists/' and converts them to the pipeline
format (Song Name, Artist, Release Year, ...). Only playlists not already present
in data/playlists/ are shown for selection.

Exportify column mapping:
    Track Name      → Song Name
    Artist Name(s)  → Artist  (full string kept; Exportify separates multiple artists with ';')
    Release Date    → Release Year  (YYYY extracted from YYYY-MM-DD)

Usage:
    python scripts/phase1_exportify.py              # interactive selection
    python scripts/phase1_exportify.py --all        # import all new playlists
    python scripts/phase1_exportify.py --playlist "Playlist Name"
"""
import argparse
import csv
import os
from utils.csv_ops import get_csv_path, write_playlist_csv, read_playlist_csv
from utils.cli import select_playlist

EXPORTIFY_DIR = "exported playlists"


def filename_to_name(filename: str) -> str:
    """Convert Exportify filename to playlist name: 'Birth_Year.csv' → 'Birth Year'."""
    return os.path.splitext(filename)[0].replace("_", " ")


def get_available_playlists() -> list[dict]:
    """Return Exportify playlists not yet imported into data/playlists/."""
    if not os.path.exists(EXPORTIFY_DIR):
        return []
    available = []
    for filename in sorted(os.listdir(EXPORTIFY_DIR)):
        if not filename.endswith(".csv"):
            continue
        name = filename_to_name(filename)
        if not read_playlist_csv(get_csv_path(name)):
            available.append({"name": name, "filename": filename})
    return available


def read_exportify_csv(filepath: str) -> list[dict]:
    """Read an Exportify CSV and return pipeline row dicts."""
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row.get("Artist Name(s)", "").strip()
            release_date = row.get("Release Date", "")
            release_year = release_date[:4] if release_date else ""
            rows.append({
                "Song Name": row.get("Track Name", ""),
                "Artist": artist,
                "Release Year": release_year,
                "Music Video Found": "",
                "Added to YT Playlist": "",
                "YouTube URL": "",
            })
    return rows


def process_playlist(entry: dict):
    name = entry["name"]
    src = os.path.join(EXPORTIFY_DIR, entry["filename"])
    dest = get_csv_path(name)
    print(f"  Importing '{name}'...")
    rows = read_exportify_csv(src)
    if not rows:
        print(f"  No tracks found in {src}. Skipping.")
        return
    write_playlist_csv(dest, rows)
    print(f"  Written {len(rows)} tracks to {dest}")


def main():
    parser = argparse.ArgumentParser(description="Phase 1 (Exportify): import playlist CSVs")
    parser.add_argument("--playlist", help="Playlist name to import")
    parser.add_argument("--all", action="store_true", help="Import all new playlists")
    args = parser.parse_args()

    available = get_available_playlists()
    if not available:
        print(f"No new playlists found in '{EXPORTIFY_DIR}/'.")
        print("All playlists may already be imported, or the directory is empty.")
        return

    names = [p["name"] for p in available]
    name_to_entry = {p["name"]: p for p in available}
    print(f"Found {len(available)} new playlist(s) to import.")

    if args.all:
        selected = available
    else:
        chosen_names = select_playlist(names, args.playlist)
        selected = available if not chosen_names else [name_to_entry[n] for n in chosen_names]

    for entry in selected:
        process_playlist(entry)

    print("Phase 1 (Exportify) complete.")


if __name__ == "__main__":
    main()
