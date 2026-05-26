import os
import tempfile
from unittest.mock import patch
import pytest
from utils.csv_ops import (
    PLAYLIST_COLUMNS,
    write_playlist_csv,
    read_playlist_csv,
    get_csv_path,
    lookup_summary_url,
    upsert_summary,
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


# lookup_summary_url + upsert_summary
def test_lookup_summary_url_returns_none_when_file_missing(tmp_path):
    with patch("utils.csv_ops.SUMMARY_FILE", str(tmp_path / "summary.csv")):
        assert lookup_summary_url("Anything") is None


def test_lookup_summary_url_returns_url_for_existing_row(tmp_path):
    summary = tmp_path / "summary.csv"
    with patch("utils.csv_ops.SUMMARY_FILE", str(summary)):
        upsert_summary("Confidence", 6, 5, "https://youtube.com/playlist?list=PL123")
        assert lookup_summary_url("Confidence") == "https://youtube.com/playlist?list=PL123"


def test_lookup_summary_url_returns_none_for_missing_playlist(tmp_path):
    summary = tmp_path / "summary.csv"
    with patch("utils.csv_ops.SUMMARY_FILE", str(summary)):
        upsert_summary("Confidence", 6, 5, "https://youtube.com/playlist?list=PL123")
        assert lookup_summary_url("Other Playlist") is None


def test_upsert_summary_replaces_existing_row(tmp_path):
    summary = tmp_path / "summary.csv"
    with patch("utils.csv_ops.SUMMARY_FILE", str(summary)):
        upsert_summary("Confidence", 6, 5, "https://youtube.com/playlist?list=PL123")
        upsert_summary("Confidence", 6, 6, "https://youtube.com/playlist?list=PL123")
        contents = summary.read_text(encoding="utf-8")
    # Only one Confidence row, with updated video count
    assert contents.count("Confidence") == 1
    assert "6,6," in contents
