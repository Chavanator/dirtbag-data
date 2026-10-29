"""Tests del almacenamiento RAW local (append-only)."""

from dirtbag_data.storage.raw import LocalRawStorage


def test_save_returns_key_and_writes_file(tmp_path):
    storage = LocalRawStorage(tmp_path)
    key = storage.save(
        "thecrag",
        "https://www.thecrag.com/en/climbing/mexico/el-salto/route/11939401",
        "<html>uno</html>",
    )
    assert key.startswith("thecrag/")
    assert key.endswith(".html")
    assert "11939401" in key or "route" in key
    path = tmp_path / key
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "<html>uno</html>"


def test_append_only_never_overwrites(tmp_path):
    storage = LocalRawStorage(tmp_path)
    url = "https://www.thecrag.com/page"
    key1 = storage.save("thecrag", url, "version-1")
    key2 = storage.save("thecrag", url, "version-2")  # mismo día → misma clave
    assert key1 == key2
    assert (tmp_path / key1).read_text(encoding="utf-8") == "version-1"
