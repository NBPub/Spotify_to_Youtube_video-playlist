# Playlist Access — Spotify's 2024 API Restrictions

## What changed

In late 2024, Spotify revised the permissions model for the Web API. Apps newly registered after the change have **limited read access to playlists owned by other accounts**. Previously, any authenticated app could read any public playlist's tracks; after the change, basic apps (apps not explicitly granted extended quota via Spotify's review process) receive a `403 Forbidden` when calling the `/playlists/{id}/tracks` endpoint on playlists they do not own.

Your own playlists remain accessible regardless. The restriction only applies to shared, third-party, or service-owned playlists.

## Why this matters here

Music League playlists are owned by the `MusicLeague` Spotify account, not by individual players. Under the new permissions, a basic app — including `phase1_spotify.py` in this project — cannot read their tracks, even when the playlist is public and the user follows it. This blocks the entire pipeline at the source-data step. 
Multiple work-arounds were attempted to no avail.

## The Exportify workaround

[Exportify](https://exportify.net) is a web app that pre-dates the 2024 API change and retains its original, broader Spotify scopes. When you log into Exportify with your Spotify account, it can still read tracks from any playlist your account has access to — including third-party-owned playlists.

In this project, Exportify is the primary Phase 1 source. The trade-off is that the download step is manual: visit the site, log in, click *Export* for each playlist(s) of interest, and add to folder. Everything downstream remains automated.

The pre-2024 permissions Exportify uses are exactly what newer apps no longer get. This is an explicit choice by Spotify — presumably to clamp down on scraping or large-scale data export — and Exportify is grandfathered in for as long as Spotify chooses to leave it that way. There is no guarantee this remains a viable workaround indefinitely. If Exportify is shut down or its scopes are revoked, the primary entry point of this pipeline goes with it.
