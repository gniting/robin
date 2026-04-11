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

    topic_file = robin_env["topics_dir"] / "ai-reasoning.md"
    content = topic_file.read_text(encoding="utf-8")
    assert f"id: {output['id']}" in content
    assert "description: Advice on keeping prose direct and readable. A useful writing principle to revisit." in content
    assert "Write clearly." in content

    index = load_index()
    assert output["id"] in index["items"]
    assert index["items"][output["id"]]["topic"] == "ai-reasoning"


def test_add_entry_respects_explicit_state_dir_without_env(robin_env, monkeypatch, capsys):
    monkeypatch.delenv("ROBIN_STATE_DIR", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--state-dir",
            str(robin_env["state_dir"]),
            "--topic",
            "AI Reasoning",
            "--content",
            "State dir should be explicit.",
            "--description",
            "Regression coverage for explicit state directory usage without an environment variable.",
            "--json",
        ],
    )

    add_entry.main()
    output = json.loads(capsys.readouterr().out)

    topic_file = robin_env["topics_dir"] / "ai-reasoning.md"
    content = topic_file.read_text(encoding="utf-8")
    assert f"id: {output['id']}" in content
    assert "State dir should be explicit." in content


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
    copied = robin_env["state_dir"] / output["media_source"]

    assert output["entry_type"] == "image"
    assert copied.exists()
    assert copied.read_bytes() == b"fake-image"


def test_add_text_entry_can_attach_local_image(robin_env, monkeypatch, capsys):
    image_path = robin_env["tmp_path"] / "screenshot.png"
    image_path.write_bytes(b"fake-screenshot")

    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "Wisdom",
            "--content",
            "Filed this screenshot to wisdom.",
            "--description",
            "A text note with a local screenshot attached for later context.",
            "--media-path",
            str(image_path),
            "--json",
        ],
    )

    add_entry.main()
    output = json.loads(capsys.readouterr().out)
    copied = robin_env["state_dir"] / output["media_source"]
    topic_file = robin_env["topics_dir"] / "wisdom.md"
    content = topic_file.read_text(encoding="utf-8")

    assert output["entry_type"] == "text"
    assert output["media_source"].startswith("media/wisdom/")
    assert copied.exists()
    assert copied.read_bytes() == b"fake-screenshot"
    assert f"id: {output['id']}" in content
    assert f"media_source: {output['media_source']}" in content
    assert "media_kind:" not in content
    assert "creator:" not in content
    assert "published_at:" not in content
    assert "summary:" not in content


def test_add_text_entry_rejects_media_url(robin_env, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "Wisdom",
            "--content",
            "This should not attach a remote URL.",
            "--description",
            "A text note attempting to attach a media URL.",
            "--media-url",
            "https://example.com/image.png",
            "--json",
        ],
    )

    try:
        add_entry.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit for text media URL rejection")

    output = json.loads(capsys.readouterr().out)
    assert "Text entries do not accept --media-url" in output["error"]


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


def test_add_entry_rejects_reserved_separator_in_body(robin_env, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "AI Reasoning",
            "--content",
            "First line.\n***\nSecond line.",
            "--description",
            "Advice worth revisiting.",
            "--json",
        ],
    )

    try:
        add_entry.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit for reserved separator rejection")

    output = json.loads(capsys.readouterr().out)
    assert "standalone '***' line" in output["error"]


def test_add_entry_rejects_reserved_separator_at_end_of_body(robin_env, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "AI Reasoning",
            "--content",
            "First line.\n***",
            "--description",
            "Advice worth revisiting.",
            "--json",
        ],
    )

    try:
        add_entry.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit for trailing reserved separator rejection")

    output = json.loads(capsys.readouterr().out)
    assert "standalone '***' line" in output["error"]
