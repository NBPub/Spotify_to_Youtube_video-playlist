# Pipeline data

Auto-populated by the scripts. Nothing in here is tracked.

- `playlists/<name>.csv` — Pipeline-format track list, written by Phase 1.
- `summary.csv` — Master summary table, updated by Phase 3.
- `quota_state.json` — YouTube API daily quota usage (persists across runs on the same day, resets at the next UTC midnight).

All files in this folder are gitignored except this README.
