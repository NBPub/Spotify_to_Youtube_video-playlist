# Spotify → YouTube Playlist Pipeline

Mirrors Spotify playlists as Unlisted YouTube playlists via [Exportify](https://exportify.net) CSV exports.

## Workflow
1. Download CSVs from exportify.net → `exported playlists/`
2. `python -m scripts.phase1_exportify --all` — convert to pipeline format
3. `python -m scripts.phase2_yt_search --playlist "Name"` — match YouTube videos
4. `python -m scripts.phase3_yt_playlist --playlist "Name"` — create Unlisted playlist
5. `python -m scripts.phase4_summary` — view summary

See [USAGE.md](USAGE.md) for full command reference, batching, resume options, and quota details.

## Setup
1. `cp .env.example .env` and set `MATCH_STRICTNESS` if desired
2. Download OAuth credentials from Google Cloud Console → save as `client_secrets.json` (see `client_secrets.json.example` for structure)
3. `pip install -r requirements.txt`
4. First phase 2 run prompts for YouTube OAuth login in your browser

## Key behavior
- **Resumable:** Scripts skip processed rows — safe to re-run after stopping.
- **Match strictness:** `low`/`medium`/`high` via `MATCH_STRICTNESS` in `.env`. Medium is the default. `high` is artist-strict; official-music-video filtering is pending.
- **Quota:** YouTube allows 10,000 units/day; usage persists in `data/quota_state.json` and resets automatically on a new day.
- **Censored words:** `F**k`-style censored YouTube titles match uncensored song names via per-character `_` wildcards at all strictness levels. Trailing censorship (`f***`) is not handled.
- **HTML entities:** YouTube titles often contain `&amp;`, `&quot;`, `&#39;` — decoded before matching.

## Phase 1 alternatives
| Script | Source | Use case |
|--------|--------|---------|
| `phase1_exportify.py` | `exported playlists/*.csv` | **Primary** — works for any Spotify playlist including third-party owned |
| `phase1_spotify.py` | Spotify Web API | User-owned playlists only (post-2024 API restriction) |
| `phase1_musicleague.py` | Music League API | Non-functional — endpoints appear deprecated |

## Background

Spotify's 2024 API changes block basic apps from reading tracks on playlists owned by other accounts. Many Music League playlists are owned by the MusicLeague Spotify account, so `phase1_spotify.py` returns 403 for them. Exportify (a pre-2024 app with grandfathered permissions) reads them successfully and is the primary entry point. An attempt to use Music League's own API also failed.

## Auth files (gitignored)
`token.json` (YouTube), `.cache` (Spotify PKCE), `client_secrets.json`, `.env`. Delete `token.json` to force YouTube re-auth.
