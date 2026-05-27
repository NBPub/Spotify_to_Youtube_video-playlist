# Usage Guide

**Contents**

- [Workflow](#typical-workflow)
- [Phases](#individual-phases)
- [Selection](#selection-options)
- [Quota](#quota)
- [Re-authentication](#re-authentication)
- [Phase 1 Alternatives](#phase-1-alternatives)

## Typical Workflow

### Step 1 — Download from Exportify (manual)
1. Visit [exportify.net](https://exportify.net) and log in with Spotify. Note [Phase 1 Alternatives](#phase-1-alternatives).
2. Download CSVs for new playlists
3. Place them in the `exported playlists/` directory

### Step 2 — Activate the virtual environment
```bash
source venv/Scripts/activate
```

### Step 3 — Run the pipeline

**Full pipeline (recommended)** — imports, searches YouTube, creates playlists:
```bash
python -m scripts.run_pipeline                   # interactive playlist selection
python -m scripts.run_pipeline --all             # all new playlists in exported playlists/
python -m scripts.run_pipeline --daily-limit 5000  # custom quota budget (default: 9000)
```

### Retrying Video Matching

Songs that fail to find a suitable match — visible as `✗` lines in the console output of [phase 2](#phase-2--search-youtube-for-matching-videos) — can often be matched after lowering strictness. The process:

1. **Lower the match strictness.** Edit `.env` and set `MATCH_STRICTNESS=low` (or `medium` if you were running on `high`).

2. **Clear the row in the playlist CSV** at `data/playlists/<Name>.csv` for the unmatched track(s). Delete the values in two columns:
   - `Music Video Found` (the `FALSE` marker that would otherwise cause the row to be skipped)
   - `YouTube URL` (any partial state)

   Phase 2 skips rows that already have any `Music Video Found` value, so emptying the cell is what forces a retry. This is safe — all phases are designed to be re-run, and rows you don't touch will continue to be skipped.

3. **Re-run phase 2** on that playlist:
   ```bash
   python -m scripts.phase2_yt_search --playlist "Name"
   ```
   Only the cleared row(s) will be re-processed.

4. **Add the newly matched video(s) to the existing YouTube playlist** by running phase 3 with `--resume-playlist-id`:
   ```bash
   python -m scripts.phase3_yt_playlist --playlist "Name" --resume-playlist-id <playlist_id>
   ```
   `<playlist_id>` is the `list=` value from the URL in `data/summary.csv`. Without `--resume-playlist-id`, phase 3 detects the existing `Added to YT Playlist = TRUE` rows and exits early to avoid creating a duplicate playlist.

---

## Individual Phases

Run phases separately when resuming, re-processing, or debugging.

### Phase 1 — Import Exportify CSVs
Reads `exported playlists/*.csv`, skips already-imported playlists, writes to `data/playlists/`.
```bash
python -m scripts.phase1_exportify               # interactive selection
python -m scripts.phase1_exportify --all         # import all new playlists
python -m scripts.phase1_exportify --playlist "Name"
```

### Phase 2 — Search YouTube for matching videos
Searches YouTube for each song and records the best matching upload (official music video,
official audio, lyric video, etc.). Checks the top 3 results and uses the first suitable
match. Skips rows already processed.
```bash
python -m scripts.phase2_yt_search               # interactive selection
python -m scripts.phase2_yt_search --playlist "Name"
python -m scripts.phase2_yt_search --all
python -m scripts.phase2_yt_search --playlist "Name" --daily-limit 5000
```

Match strictness is set via `MATCH_STRICTNESS` in `.env`:

| Value | Behavior |
|-------|-----------|
| `low` | Fuzzy song match only — all parenthetical content stripped from song name (e.g. `(Interlude)`, `(Album Version)`), then all unique remaining words must appear in the title (order-independent, handles compound words, no artist check) |
| `medium` | Song title + any credited artist matches title or channel *(default)* |
| `high` | Song title + primary artist only matches title or channel *(see note below)* |

> **`high` strictness — pending development:** The intent is to optimize this mode for official
> music videos specifically (e.g. requiring "Official Music Video" in the title or restricting to
> verified artist channels). The artist-only logic is in place but the official video filtering
> has not yet been implemented.

### Phase 3 — Create YouTube playlists
Creates an Unlisted YouTube playlist and adds matched videos. Skips rows already added.
```bash
python -m scripts.phase3_yt_playlist             # interactive selection
python -m scripts.phase3_yt_playlist --playlist "Name"
python -m scripts.phase3_yt_playlist --all
```

**Resuming a partially-completed playlist** (e.g. after a quota cutoff mid-run):
```bash
python -m scripts.phase3_yt_playlist --playlist "Name" --resume-playlist-id PLxxxxxxxxxxxxxxx
```
The playlist ID is the `list=` value from the URL in `data/summary.csv`.

### Phase 4 — View summary
Prints `data/summary.csv` — playlist names, track counts, video counts, and YouTube URLs.
```bash
python -m scripts.phase4_summary
```

---

## Selection Options

All scripts that accept `--playlist` support:
- **Exact name**: `--playlist "A Family Affair"`
- **Comma-separated**: `--playlist "Playlist One,Playlist Two"`
- **All**: `--all` flag, or enter `0` in the interactive menu
- **Interactive menu**: omit `--playlist` to pick from a numbered list

---

## Quota

YouTube Data API v3 allows **10,000 units/day**. The pipeline defaults to using 9,000, leaving headroom.

| Operation | Cost |
|-----------|------|
| YouTube search (Phase 2) | 100 units/song |
| Create playlist (Phase 3) | 50 units |
| Add video to playlist (Phase 3) | 50 units/video |

At the default 9,000-unit budget:
- ~90 songs searchable per day (Phase 2)
- ~175 videos addable per day (Phase 3)

Scripts estimate quota before each playlist and stop gracefully if insufficient. All phases are resumable — re-run the next day and already-processed rows are skipped automatically.

**Quota persistence:** Usage is saved to `data/quota_state.json` after every API call and restored at the start of the next run on the same day. If you ran phase 2 earlier and used 3,000 units, a new phase 3 run will start with 3,000 already accounted for. The count resets automatically on a new day. The `--daily-limit` flag is the cap for total usage on that day across all runs.

---

## Re-authentication

If YouTube auth expires or you need to force a new login, delete `token.json` and re-run any phase — it will prompt for OAuth login in your browser.


# Phase 1 Alternatives

Two alternative entry points to Phase 1 are included. Both require **Spotify API credentials** in `.env` (`SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`) — see [docs/Services Used.md](docs/Services%20Used.md#services-used) for app registration and redirect-URI setup.

## `phase1_spotify.py` — Spotify Web API

Reads playlists you own directly from the Spotify Web API, skipping the Exportify download. Writes pipeline-format CSVs to `data/playlists/`.

```bash
python -m scripts.phase1_spotify                  # interactive selection
python -m scripts.phase1_spotify --playlist "Name"
python -m scripts.phase1_spotify --all
```

Only works for playlists owned by your authenticated account — Spotify's 2024 API restrictions block reading third-party-owned playlists (see [docs/Playlist Access.md](docs/Playlist%20Access.md#playlist-access--spotifys-2024-api-restrictions)). Optionally set `PLAYLIST_FOLDER` in `.env` to restrict the import to a single Spotify folder.

## `phase1_musicleague.py` — Music League API (deprecated)

Attempted integration with the Music League API. **Not currently functional** — the targeted endpoints appear to have been deprecated. Kept as a historical reference. Spotify API credentials in `.env` are still required because the script uses the Spotify API to fetch the actual track data after retrieving playlist IDs from Music League.