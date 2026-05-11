# Usage Guide

## Typical Workflow

### Step 1 — Download from Exportify (manual)
1. Visit [exportify.net](https://exportify.net) and log in with Spotify
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

| Value | Behaviour |
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
