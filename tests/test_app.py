import importlib
import urllib.parse

from fastapi.testclient import TestClient


def _reload_app_module():
    """Reload the application module to reset in-memory state between tests."""
    mod = importlib.import_module("src.app")
    importlib.reload(mod)
    return mod


def test_get_activities_returns_all_activities():
    # Arrange
    app_mod = _reload_app_module()
    client = TestClient(app_mod.app)

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    # basic smoke checks for known activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant():
    # Arrange
    app_mod = _reload_app_module()
    client = TestClient(app_mod.app)
    activity = "Chess Club"
    new_email = "tester+signup@mergington.edu"

    # ensure clean start
    assert new_email not in app_mod.activities[activity]["participants"]

    # Act
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(new_email)}"
    resp = client.post(url)

    # Assert
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Signed up {new_email} for {activity}"
    # verify participant was added
    get_resp = client.get("/activities")
    assert new_email in get_resp.json()[activity]["participants"]


def test_duplicate_signup_returns_400():
    # Arrange
    app_mod = _reload_app_module()
    client = TestClient(app_mod.app)
    activity = "Chess Club"
    existing_email = app_mod.activities[activity]["participants"][0]

    # Act
    url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(existing_email)}"
    resp = client.post(url)

    # Assert
    assert resp.status_code == 400
    assert "already signed up" in resp.json().get("detail", "")


def test_remove_participant_unsubscribes_student():
    # Arrange
    app_mod = _reload_app_module()
    client = TestClient(app_mod.app)
    activity = "Chess Club"
    to_remove = app_mod.activities[activity]["participants"][0]

    # precondition
    assert to_remove in app_mod.activities[activity]["participants"]

    # Act
    url = f"/activities/{urllib.parse.quote(activity)}/participants?email={urllib.parse.quote(to_remove)}"
    resp = client.delete(url)

    # Assert
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Removed {to_remove} from {activity}"
    get_resp = client.get("/activities")
    assert to_remove not in get_resp.json()[activity]["participants"]
