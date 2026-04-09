from __future__ import annotations

import json
from pathlib import Path

from robin.config import load_index
from scripts import add_entry


def test_add_entry_writes_markdown_and_index(robin_env, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "AI Reasoning",
            "--content",
            "Write clearly.",
            "--description",
            "Advice on keeping prose direct and readable. A useful writing principle to revisit.",
            "--source",
            "https://example.com",
            "--tags",
            "writing,clarity",
            "--json",
        ],
    )

    add_entry.main()
    output = json.loads(capsys.readouterr().out)

    topic_file = robin_env["vault_path"] / "topics" / "ai-reasoning.md"
    content = topic_file.read_text(encoding="utf-8")
    assert f"id: {output['id']}" in content
    assert "description: Advice on keeping prose direct and readable. A useful writing principle to revisit." in content
    assert "Write clearly." in content

    index = load_index()
    assert output["id"] in index["items"]
    assert index["items"][output["id"]]["topic"] == "ai-reasoning"


def test_add_image_entry_copies_media(robin_env, monkeypatch, capsys):
    image_path = robin_env["tmp_path"] / "poem.png"
    image_path.write_bytes(b"fake-image")

    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "Poetry",
            "--entry-type",
            "image",
            "--media-path",
            str(image_path),
            "--description",
            "A photographed poem excerpt with enough context to remember why it matters.",
            "--creator",
            "Mary Oliver",
            "--published-at",
            "1986",
            "--summary",
            "An excerpt centered on attention and observation.",
            "--content",
            "Opening lines from the page.",
            "--json",
        ],
    )

    add_entry.main()
    output = json.loads(capsys.readouterr().out)
    copied = robin_env["vault_path"] / output["media_source"]

    assert output["entry_type"] == "image"
    assert copied.exists()
    assert copied.read_bytes() == b"fake-image"


def test_add_video_url_entry_accepts_reference(robin_env, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "Talks",
            "--entry-type",
            "video",
            "--media-url",
            "https://www.youtube.com/watch?v=abc123",
            "--description",
            "A talk to revisit later for the framing and examples.",
            "--creator",
            "Speaker Name",
            "--published-at",
            "2025-01-01",
            "--summary",
            "A concise summary of the talk.",
            "--json",
        ],
    )

    add_entry.main()
    output = json.loads(capsys.readouterr().out)
    assert output["entry_type"] == "video"
    assert output["media_source"] == "https://www.youtube.com/watch?v=abc123"


def test_add_uploaded_video_rejected(robin_env, monkeypatch, capsys):
    video_path = robin_env["tmp_path"] / "clip.mp4"
    video_path.write_bytes(b"fake-video")

    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "Talks",
            "--entry-type",
            "video",
            "--media-path",
            str(video_path),
            "--description",
            "A talk to revisit later for the framing and examples.",
            "--creator",
            "Speaker Name",
            "--published-at",
            "2025-01-01",
            "--summary",
            "A concise summary of the talk.",
            "--json",
        ],
    )

    try:
        add_entry.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit for uploaded video rejection")

    output = json.loads(capsys.readouterr().out)
    assert "Uploaded or local video files are not supported" in output["error"]
