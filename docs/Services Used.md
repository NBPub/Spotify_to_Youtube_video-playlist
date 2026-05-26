# Services Used

## [Spotify Web API](https://developer.spotify.com/documentation/web-api)

The official API for reading Spotify playlists, tracks, and audio features.

- Create a Spotify app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) to obtain a client ID and client secret.
- **Redirect URI.** When configuring the Spotify app, add `http://127.0.0.1:8888/callback` as a Redirect URI under the app's *Settings* page. This must match exactly what the script uses ([`utils/spotify_auth.py`](../utils/spotify_auth.py)). Two common gotchas:
  - Use `127.0.0.1`, not `localhost` — Spotify no longer accepts `localhost` for new apps. The script and the app config both need the literal IP.
  - The port (`8888`) and path (`/callback`) are part of the match — partial matches don't count.
- This project uses Spotify auth **only for `phase1_spotify.py`**, which reads playlists owned by your own account. The primary Exportify-based workflow does not require Spotify credentials.
- See [Playlist Access](Playlist%20Access.md) for the 2024 API restrictions that motivated using Exportify as the primary entry point.

## [YouTube Data API v3](https://developers.google.com/youtube/v3)

Used by every pipeline phase after Phase 1 — search for videos, create playlists, add videos.

- Create a project at [Google Cloud Console](https://console.cloud.google.com/), enable "YouTube Data API v3", and download OAuth 2.0 credentials as `client_secrets.json`. See [`client_secrets.json.example`](../client_secrets.json.example) for the expected structure.
- Quota costs: 100 units per search (`search.list`), 50 units per playlist mutation (`playlists.insert`, `playlistItems.insert`). Daily budget is 10,000 units — roughly 90 search operations or 175 playlist add operations per day.
- First run of Phase 2 opens a browser for OAuth login; the resulting `token.json` is reused until it expires. Delete it to force a fresh login.

## Exportify

[Exportify](https://exportify.net) is a third-party web app that exports Spotify playlists as CSV files. It pre-dates Spotify's 2024 API tightening and retains grandfathered permissions that let it read any playlist your Spotify account can see — including third-party-owned playlists like Music League's.

In this project, Exportify is the **primary playlist source**. The download step is manual (visit the site, log in with Spotify, click *Export* for each playlist of interest), but everything downstream is automated.

## Music League API (not used)

[Music League](https://musicleague.com) used to expose API-looking endpoints (e.g. `app.musicleague.com/api/v1/leagues/<id>`) that returned league, round, and submission data. As of this project's development, those endpoints return errors and appear to be deprecated. An attempt to use them as a Phase 1 source was abandoned. The unfinished implementation lives at [`scripts/phase1_musicleague.py`](../scripts/phase1_musicleague.py) as a historical reference.
