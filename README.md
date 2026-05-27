# Spotify → YouTube Video Playlist

Collection of Python scripts to mirror Spotify playlists as Unlisted YouTube playlists, semi-automatically\*. 

\* *If you are using this for playlists you created or registered with the Spotify API before v2, chances are that you can run this automatically*

Personal tool, originally built to recreate [Music League](https://musicleague.com) playlists on YouTube. 
Given Spotify API limitations, it makes use [Exportify](https://exportify.net) for the Spotify-side export step.

> Not affiliated with or endorsed by Spotify, YouTube, Exportify, or Music League.

> Created interactively with Claude Code and serves as a demonstration of my usage. Some code was manually reviewed, but only sparingly. Makes use of [superpowers](https://github.com/obra/superpowers) plugin.

[MIT Licensed](LICENSE) · [Contributing](CONTRIBUTING.md#contributing)

**Contents**

- [What it does](#what-it-does)
- [Quick start](#quick-start)
- [Features](#features)
- [Packages](#python-packages)
- [Phases](#pipeline-phases)

## What it does

The pipeline reads Spotify playlist(s) or reads exported CSV(s),  searches YouTube for each track, picks the best matching video (official music video, official audio, lyric video, or other suitable upload), and assembles an Unlisted YouTube playlist of the matched videos. 
CSV summaries are generated for each step.

Playlist matching can be adjusted with environmental variables. "Strict" matching is in development to only match actual music videos.

## Quick start

See [docs](docs/Services%20Used.md#services-used) for details about required API registrations and authentication details.

```bash
git clone https://github.com/NBPub/Spotify_to_Youtube_video-playlist
cd Spotify_to_Youtube_video-playlist
python -m venv venv && source venv/Scripts/activate   # Windows; use venv/bin/activate on Unix
pip install -r requirements.txt
cp .env.example .env
# Add Spotify API credentials to .env file for alternative phase 1
# Download OAuth credentials from Google Cloud Console → save as client_secrets.json
#   (see client_secrets.json.example for structure)
python -m scripts.run_pipeline
```

Detailed setup and per-phase commands: [USAGE.md](USAGE.md#usage-guide). Architecture and conventions: [CLAUDE.md](CLAUDE.md#spotify--youtube-playlist-pipeline).

## Features

- Four-phase pipeline (import → match → create → summarize)
- Configurable match strictness (`low` / `medium` / `high`)
- Thoughtful logic to work with song matching pitfalls
  - Multi-artist handling (semicolon-separated Exportify format)
  - Censored-word matching (`F**k` ≈ `Fuck` via per-character wildcards)
  - HTML entity decoding in YouTube titles
- Tracks YouTube API usage across runs (10,000 units/day budget) and provides warnings when quota is low
- Resumable — scripts skip already-processed rows
- Case-insensitive playlist name matching
- Batch processing (`--all`, comma-separated names)

## Python Packages

- Python 3.10+
- `google-api-python-client` for YouTube Data API v3
- `spotipy` (optional, for `phase1_spotify.py` only)
- `pytest` for tests

[list](requirements.txt)

## Pipeline phases

| Phase | Script | YT API Unit Cost |
|-------|--------|------|
| 1 | `phase1_exportify.py` — read Exportify CSVs into pipeline format | Free |
| 2 | `phase2_yt_search.py` — search YouTube for each track | 100 units/song |
| 3 | `phase3_yt_playlist.py` — create Unlisted playlist and add videos | 50 units/op |
| 4 | `phase4_summary.py` — print master summary CSV | Free |

*approximately 10,000 YT API units provided with free usage*

### Phase 1 Alternatives

***Why***

Spotify's 2024 API restrictions prevent basic apps from reading tracks on playlists owned by other accounts — including Music League's playlists. [Exportify](https://exportify.net), a pre-2024 app with grandfathered permissions, still works. This pipeline takes Exportify's CSVs and does the rest.

- For playlists on your Spotify account that you've created or have ownership of, you can use `phase1_spotify.py`. Note that the [Spotify API](https://developer.spotify.com/documentation/web-api) is required.
  - Limits amount of playlists fetched by only searching one folder. In Spotify, add your playlists to a folder of your choosing and then specify in `.env`.
- Untested usage of the deprecated Music League API is contained in `phase1_musicleague.py`. Spotify API still required to fetch track data.
- See more details [here](docs/Code.md#phase-1-alternatives)