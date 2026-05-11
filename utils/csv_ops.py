import csv
import os

SUMMARY_FILE = os.path.join("data", "summary.csv")
SUMMARY_COLUMNS = ["Playlist Name", "Tracks", "Videos", "YouTube Playlist URL"]

PLAYLIST_COLUMNS = [
    "Song Name",
    "Artist",
    "Release Year",
    "Music Video Found",
    "Added to YT Playlist",
    "YouTube URL",
]


def get_csv_path(playlist_name: str) -> str:
    return os.path.join("data", "playlists", f"{playlist_name}.csv")


def read_playlist_csv(filepath: str) -> list[dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_playlist_csv(filepath: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PLAYLIST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in PLAYLIST_COLUMNS})


def upsert_summary(playlist_name: str, tracks: int, videos: int, youtube_url: str) -> None:
    """Add or update a playlist entry in data/summary.csv."""
    os.makedirs(os.path.dirname(SUMMARY_FILE), exist_ok=True)
    rows = []
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    entry = {
        "Playlist Name": playlist_name,
        "Tracks": str(tracks),
        "Videos": str(videos),
        "YouTube Playlist URL": youtube_url,
    }
    for i, row in enumerate(rows):
        if row["Playlist Name"] == playlist_name:
            rows[i] = entry
            break
    else:
        rows.append(entry)
    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
