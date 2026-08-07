from pathlib import Path

import pytest

from app.core.exceptions import DomainError
from app.storage.local import LocalStorageService


def test_local_storage_validates_and_contains_paths(tmp_path: Path) -> None:
    storage = LocalStorageService(tmp_path / "uploads")
    name = storage.save(original_name="note.txt", content_type="text/plain", data=b"hello")
    assert storage.read(name) == b"hello"
    storage.delete(name)
    assert not (tmp_path / "uploads" / name).exists()
    with pytest.raises(DomainError):
        storage.save(original_name="../escape.txt", content_type="text/plain", data=b"x")
    with pytest.raises(DomainError):
        storage.save(original_name="bad.exe", content_type="application/octet-stream", data=b"x")
    with pytest.raises(DomainError):
        storage.save(
            original_name="big.txt", content_type="text/plain", data=b"x" * (10 * 1024 * 1024 + 1)
        )
