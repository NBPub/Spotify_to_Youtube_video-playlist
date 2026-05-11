# Spotify → YouTube Playlist Mirror

Mirror Spotify playlists as Unlisted YouTube playlists, semi-automatically.

Personal tool, originally built to recreate [Music League](https://musicleague.com) playlists on YouTube. Uses [Exportify](https://exportify.net) for the Spotify-side export step.

> Not affiliated with or endorsed by Spotify, YouTube, Exportify, or Music League.

## What it does

Given a Spotify playlist exported as CSV, the pipeline searches YouTube for each track, picks the best matching video (official music video, official audio, lyric video, or other suitable upload), and assembles an Unlisted YouTube playlist of the matched videos.

## Why

Spotify's 2024 API restrictions prevent basic apps from reading tracks on playlists owned by other accounts — including Music League's playlists. [Exportify](https://exportify.net), a pre-2024 app with grandfathered permissions, still works. This pipeline takes Exportify's CSVs and does the rest.

## Quick start

```bash
git clone https://github.com/NBPub/Spotify_to_Youtube_video-playlist
cd Spotify_to_Youtube_video-playlist
python -m venv venv && source venv/Scripts/activate   # Windows; use venv/bin/activate on Unix
pip install -r requirements.txt
cp .env.example .env
# Download OAuth credentials from Google Cloud Console → save as client_secrets.json
#   (see client_secrets.json.example for structure)
python -m scripts.run_pipeline
```

Detailed setup and per-phase commands: [USAGE.md](USAGE.md). Architecture and conventions: [CLAUDE.md](CLAUDE.md).

## Features

- Four-phase pipeline (import → match → create → summarize)
- Configurable match strictness (`low` / `medium` / `high`)
- Multi-artist handling (semicolon-separated Exportify format)
- Censored-word matching (`F**k` ≈ `Fuck` via per-character wildcards)
- HTML entity decoding in YouTube titles
- YouTube API quota persistence across runs (10,000 units/day budget)
- Resumable — scripts skip already-processed rows
- Case-insensitive playlist name matching
- Batch processing (`--all`, comma-separated names)

## Stack

- Python 3.10+
- `google-api-python-client` for YouTube Data API v3
- `spotipy` (optional, for `phase1_spotify.py` only)
- `pytest` for tests

## Pipeline phases

| Phase | Script | Cost |
|-------|--------|------|
| 1 | `phase1_exportify.py` — read Exportify CSVs into pipeline format | Free |
| 2 | `phase2_yt_search.py` — search YouTube for each track | 100 units/song |
| 3 | `phase3_yt_playlist.py` — create Unlisted playlist and add videos | 50 units/op |
| 4 | `phase4_summary.py` — print master summary CSV | Free |

## License

[MIT](LICENSE)
