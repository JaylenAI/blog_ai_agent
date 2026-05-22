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


def test_delete_article_dir(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("del-slug", "final.md", "content")
    assert (tmp_path / "del-slug").exists()
    assert fm.delete_article_dir("del-slug") is True
    assert not (tmp_path / "del-slug").exists()


def test_delete_article_dir_nonexistent(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.delete_article_dir("nonexistent") is False


def test_backup_content(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("slug", "final.md", "# v1")
    version_id = fm.backup_content("slug")
    assert version_id is not None
    versions = fm.list_versions("slug")
    assert len(versions) == 1
    assert versions[0]["version_id"] == version_id


def test_backup_content_max_versions(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("slug", "final.md", "content")

    import time
    ids = []
    for _ in range(12):
        vid = fm.backup_content("slug", max_versions=10)
        ids.append(vid)
        time.sleep(0.002)

    versions = fm.list_versions("slug")
    assert len(versions) == 10


def test_backup_content_no_final(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.backup_content("empty-slug") is None


def test_get_version_content(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("slug", "final.md", "# version content")
    vid = fm.backup_content("slug")
    content = fm.get_version_content("slug", vid)
    assert content == "# version content"


def test_get_version_content_nonexistent(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.get_version_content("slug", "99999") is None


def test_restore_version(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    fm.write_text("slug", "final.md", "# v1 original")
    vid = fm.backup_content("slug")

    fm.write_text("slug", "final.md", "# v2 modified")
    assert fm.restore_version("slug", vid) is True
    restored = fm.read_text("slug", "final.md")
    assert restored == "# v1 original"


def test_restore_version_nonexistent(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.restore_version("slug", "99999") is False


def test_list_versions_empty(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    assert fm.list_versions("no-versions") == []


def test_diagrams_dir(tmp_path: Path) -> None:
    fm = _make_manager(tmp_path)
    path = fm.diagrams_dir("slug")
    assert path.exists()
    assert path.name == "diagrams"
