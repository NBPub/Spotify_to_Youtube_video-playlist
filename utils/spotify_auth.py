import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyPKCE, SpotifyClientCredentials

load_dotenv()

SCOPES = "playlist-read-private playlist-read-collaborative user-library-read"
REDIRECT_URI = "http://127.0.0.1:8888/callback"


def get_spotify_client() -> spotipy.Spotify:
    """User-authenticated client (PKCE). Used for listing the user's playlists."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    if not client_id:
        raise EnvironmentError("SPOTIFY_CLIENT_ID not set in .env")

    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_spotify_app_client() -> spotipy.Spotify:
    """App-level client (Client Credentials). Used for reading public playlist tracks.

    Reads any public playlist regardless of ownership — needed for third-party
    playlists (e.g. Music League) that appear in the user's library but are
    owned by a different Spotify account.
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id:
        raise EnvironmentError("SPOTIFY_CLIENT_ID not set in .env")
    if not client_secret:
        raise EnvironmentError(
            "SPOTIFY_CLIENT_SECRET not set in .env — required for reading "
            "playlists owned by third-party apps (e.g. Music League). "
            "Find it in your Spotify Developer Dashboard."
        )

    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
    )
    return spotipy.Spotify(auth_manager=auth_manager)
