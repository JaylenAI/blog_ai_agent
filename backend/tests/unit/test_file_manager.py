from pathlib import Path

from app.utils.file_manager import FileManager


def _make_manager(tmp_path: Path) -> FileManager:
    return FileManager(base_dir=tmp_path)


def test_article_dir_created(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    path = fm.article_dir("test-slug")

    assert path.exists()
    assert path.is_dir()
    assert path.name == "test-slug"


def test_images_dir_created(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    path = fm.images_dir("test-slug")

    assert path.exists()
    assert path.name == "images"


def test_write_and_read_text(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("my-post", "draft.md", "# 제목\n\n본문입니다.")

    content = fm.read_text("my-post", "draft.md")
    assert content == "# 제목\n\n본문입니다."


def test_write_and_read_json(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    data = {"title": "테스트", "tags": ["AI", "ML"]}
    fm.write_json("my-post", "meta.json", data)

    loaded = fm.read_json("my-post", "meta.json")
    assert loaded == data


def test_read_nonexistent_returns_none(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.read_text("no-slug", "no-file.md") is None
    assert fm.read_json("no-slug", "no-file.json") is None


def test_exists(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("slug", "file.txt", "data")

    assert fm.exists("slug", "file.txt") is True
    assert fm.exists("slug", "nope.txt") is False


def test_list_files(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("slug", "a.md", "aaa")
    fm.write_text("slug", "b.json", "bbb")

    files = fm.list_files("slug")
    assert "a.md" in files
    assert "b.json" in files


def test_list_files_empty(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.list_files("nonexistent") == []
