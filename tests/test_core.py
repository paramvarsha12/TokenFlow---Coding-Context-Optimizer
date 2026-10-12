
from pathlib import Path

from quotapilot.core import (
    estimate_tokens,
    prepare_task,
    scan_project,
)


def test_token_estimator():
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") > 0


def test_scan_skips_secrets(tmp_path: Path):
    (tmp_path / "app.py").write_text(
        "def delete_subject():\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "API_KEY=secret",
        encoding="utf-8",
    )

    files = scan_project(tmp_path)
    paths = {item["path"] for item in files}

    assert "app.py" in paths
    assert ".env" not in paths


def test_prepare_task_selects_relevant_files(tmp_path: Path):
    (tmp_path / "deletion.py").write_text(
        "def delete_subject(subject_id):\n"
        "    return remove_subject(subject_id)\n",
        encoding="utf-8",
    )
    (tmp_path / "weather.py").write_text(
        "def forecast_weather(city):\n"
        "    return city\n",
        encoding="utf-8",
    )

    result = prepare_task(
        tmp_path,
        "implement delete subject",
        max_tokens=2000,
    )

    paths = {item["path"] for item in result["files"]}

    assert "deletion.py" in paths
    assert "weather.py" not in paths
    assert result["estimated_tokens"] <= result["budget_tokens"]
