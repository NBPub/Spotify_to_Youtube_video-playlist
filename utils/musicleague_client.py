"""
Music League API client.

Auth: session cookie extracted from browser DevTools.
  1. Log into https://app.musicleague.com in your browser
  2. Open DevTools → Application → Cookies → app.musicleague.com
  3. Copy the value of the 'session' cookie
  4. Set MUSICLEAGUE_SESSION=<value> in .env

API base: https://app.musicleague.com/api/v1/
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ML_API_BASE = "https://app.musicleague.com/api/v1"


class MusicLeagueClient:
    def __init__(self, session_cookie: str):
        self.session = requests.Session()
        self.session.cookies.set("session", session_cookie, domain="app.musicleague.com")
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        })

    def _get(self, path: str, debug: bool = False) -> dict | list:
        url = f"{ML_API_BASE}/{path}"
        resp = self.session.get(url)
        if debug:
            print(f"  GET {url}")
            print(f"  Status: {resp.status_code}")
            try:
                print(f"  Response: {resp.json()}")
            except Exception:
                print(f"  Response (raw): {resp.text[:500]}")
        if resp.status_code == 401:
            raise PermissionError(
                "Music League session expired or invalid. "
                "Re-extract the session cookie from your browser and update MUSICLEAGUE_SESSION in .env."
            )
        resp.raise_for_status()
        return resp.json()

    def get_me(self, debug: bool = False) -> dict:
        """Get the authenticated user's profile (discovers user ID)."""
        return self._get("me", debug=debug)

    def get_user_leagues(self, user_id: str, debug: bool = False) -> list:
        data = self._get(f"users/{user_id}/leagues", debug=debug)
        if isinstance(data, list):
            return data
        for key in ("leagues", "items", "results"):
            if key in data:
                return data[key]
        return []

    def get_league(self, league_id: str, debug: bool = False) -> dict:
        return self._get(f"leagues/{league_id}", debug=debug)

    def get_rounds(self, league_id: str, debug: bool = False) -> list:
        data = self._get(f"leagues/{league_id}/rounds", debug=debug)
        if isinstance(data, list):
            return data
        for key in ("rounds", "items", "results"):
            if key in data:
                return data[key]
        return []

    def get_round_results(self, league_id: str, round_id: str, debug: bool = False) -> list:
        data = self._get(f"leagues/{league_id}/rounds/{round_id}/results", debug=debug)
        if isinstance(data, list):
            return data
        for key in ("submissions", "results", "items", "tracks"):
            if key in data:
                return data[key]
        return []


def get_ml_client() -> MusicLeagueClient:
    session_cookie = os.getenv("MUSICLEAGUE_SESSION")
    if not session_cookie:
        raise EnvironmentError(
            "MUSICLEAGUE_SESSION not set in .env. "
            "See utils/musicleague_client.py for instructions."
        )
    return MusicLeagueClient(session_cookie)
