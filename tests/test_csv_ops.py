import os
import tempfile
import pytest
from utils.csv_ops import (
    PLAYLIST_COLUMNS,
    write_playlist_csv,
    read_playlist_csv,
    get_csv_path,
)


def test_write_and_read_roundtrip():
    rows = [
        {
            "Song Name": "Blinding Lights",
            "Artist": "The Weeknd",
            "Release Year": "2019",
            "Music Video Found": "",
            "Added to YT Playlist": "",
            "YouTube URL": "",
        }
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        write_playlist_csv(path, rows)
        result = read_playlist_csv(path)
    assert len(result) == 1
    assert result[0]["Song Name"] == "Blinding Lights"
    assert result[0]["Artist"] == "The Weeknd"


def test_write_enforces_column_order():
    rows = [{"Song Name": "X", "Artist": "Y", "Release Year": "2020",
             "Music Video Found": "", "Added to YT Playlist": "",
             "YouTube URL": "https://yt.com"}]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        write_playlist_csv(path, rows)
        with open(path) as f:
            header = f.readline().strip().split(",")
    assert header == PLAYLIST_COLUMNS


def test_read_missing_columns_returns_empty_string():
    rows = [{"Song Name": "X", "Artist": "Y", "Release Year": "2020",
             "Music Video Found": "", "Added to YT Playlist": "",
             "YouTube URL": ""}]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        write_playlist_csv(path, rows)
        result = read_playlist_csv(path)
    assert result[0]["YouTube URL"] == ""


def test_get_csv_path():
    path = get_csv_path("My Playlist")
    assert path == os.path.join("data", "playlists", "My Playlist.csv")
