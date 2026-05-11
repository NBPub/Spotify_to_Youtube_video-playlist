import json
import os
import time
from datetime import date

QUOTA_STATE_FILE = os.path.join("data", "quota_state.json")


class QuotaExceededError(Exception):
    pass


class QuotaTracker:
    def __init__(self, daily_limit: int = 9000, state_file: str | None = QUOTA_STATE_FILE):
        self.daily_limit = daily_limit
        self.state_file = state_file
        self.used = self._load_used()

    def _today(self) -> str:
        return date.today().isoformat()

    def _load_used(self) -> int:
        if not self.state_file:
            return 0
        try:
            with open(self.state_file) as f:
                state = json.load(f)
            if state.get("date") == self._today():
                return int(state.get("used", 0))
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
            pass
        return 0

    def _save(self) -> None:
        if not self.state_file:
            return
        os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump({"date": self._today(), "used": self.used}, f)

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.used)

    def charge(self, units: int) -> None:
        if self.used + units > self.daily_limit:
            raise QuotaExceededError(
                f"Daily quota limit of {self.daily_limit} units reached "
                f"({self.used} used). Re-run tomorrow to continue."
            )
        self.used += units
        self._save()

    def sleep(self, seconds: float = 1.5) -> None:
        time.sleep(seconds)
