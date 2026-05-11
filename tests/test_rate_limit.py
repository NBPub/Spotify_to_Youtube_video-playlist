import json
import pytest
from datetime import date
from utils.rate_limit import QuotaTracker, QuotaExceededError


def test_charge_tracks_usage():
    tracker = QuotaTracker(daily_limit=500, state_file=None)
    tracker.charge(100)
    assert tracker.used == 100


def test_charge_multiple():
    tracker = QuotaTracker(daily_limit=500, state_file=None)
    tracker.charge(100)
    tracker.charge(200)
    assert tracker.used == 300


def test_charge_raises_when_limit_exceeded():
    tracker = QuotaTracker(daily_limit=200, state_file=None)
    tracker.charge(100)
    with pytest.raises(QuotaExceededError):
        tracker.charge(150)


def test_charge_at_exactly_limit_does_not_raise():
    tracker = QuotaTracker(daily_limit=200, state_file=None)
    tracker.charge(200)  # Should not raise


def test_remaining_units():
    tracker = QuotaTracker(daily_limit=500, state_file=None)
    tracker.charge(100)
    assert tracker.remaining == 400


def test_remaining_clamps_to_zero_when_used_exceeds_limit():
    # If persisted usage from a prior run exceeds this run's daily_limit, remaining = 0
    tracker = QuotaTracker(daily_limit=500, state_file=None)
    tracker.used = 600
    assert tracker.remaining == 0


# Persistence tests
def test_saves_state_after_charge(tmp_path):
    state_file = str(tmp_path / "quota_state.json")
    tracker = QuotaTracker(daily_limit=1000, state_file=state_file)
    tracker.charge(300)
    with open(state_file) as f:
        state = json.load(f)
    assert state["date"] == date.today().isoformat()
    assert state["used"] == 300


def test_loads_todays_state(tmp_path):
    state_file = str(tmp_path / "quota_state.json")
    with open(state_file, "w") as f:
        json.dump({"date": date.today().isoformat(), "used": 500}, f)
    tracker = QuotaTracker(daily_limit=1000, state_file=state_file)
    assert tracker.used == 500
    assert tracker.remaining == 500


def test_ignores_stale_state(tmp_path):
    state_file = str(tmp_path / "quota_state.json")
    with open(state_file, "w") as f:
        json.dump({"date": "2000-01-01", "used": 9000}, f)
    tracker = QuotaTracker(daily_limit=1000, state_file=state_file)
    assert tracker.used == 0
    assert tracker.remaining == 1000


def test_handles_missing_state_file(tmp_path):
    state_file = str(tmp_path / "quota_state.json")
    tracker = QuotaTracker(daily_limit=1000, state_file=state_file)
    assert tracker.used == 0


def test_handles_corrupt_state_file(tmp_path):
    state_file = str(tmp_path / "quota_state.json")
    with open(state_file, "w") as f:
        f.write("not valid json{{{")
    tracker = QuotaTracker(daily_limit=1000, state_file=state_file)
    assert tracker.used == 0
