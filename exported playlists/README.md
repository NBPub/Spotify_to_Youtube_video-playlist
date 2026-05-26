# Exported playlists


## Exportify

Place [Exportify](https://exportify.net) CSV exports here. Phase 1 reads them and writes pipeline-format CSVs to `../data/playlists/`.

Filenames use underscores in place of spaces — Exportify generates `Birth_Year.csv` for the playlist named `Birth Year`.

Files in this folder are gitignored and stay local (this README is the only tracked file).

## Spotify API

Access your Spotify playlists via API using the alternative [`phase1_spotify.py`](../scripts/phase1_spotify.py) script. Note that this script writes pipeline-format CSVs directly to `../data/playlists/` — it bypasses this folder entirely, since the Exportify intermediate step isn't needed when using the Spotify API directly.
