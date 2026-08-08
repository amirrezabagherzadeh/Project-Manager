from pathlib import Path
from uuid import uuid4

from app.core.exceptions import DomainError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "text/plain"})


class LocalStorageService:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, *, original_name: str, content_type: str, data: bytes) -> str:
        if not original_name or Path(original_name).name != original_name:
            raise DomainError(
                status_code=422, code="validation_error", message="نام فایل معتبر نیست."
            )
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise DomainError(
                status_code=415, code="unsupported_file_type", message="نوع فایل مجاز نیست."
            )
        if len(data) > MAX_UPLOAD_BYTES:
            raise DomainError(
                status_code=413, code="file_too_large", message="حجم فایل بیش از حد مجاز است."
            )
        storage_name = f"{uuid4().hex}{Path(original_name).suffix.lower()}"
        path = self._path(storage_name)
        path.write_bytes(data)
        return storage_name

    def read(self, storage_name: str) -> bytes:
        return self._path(storage_name).read_bytes()

    def delete(self, storage_name: str) -> None:
        self._path(storage_name).unlink(missing_ok=True)

    def _path(self, storage_name: str) -> Path:
        if Path(storage_name).name != storage_name:
            raise DomainError(status_code=404, code="resource_not_found", message="فایل پیدا نشد.")
        path = (self._root / storage_name).resolve()
        if self._root not in path.parents:
            raise DomainError(status_code=404, code="resource_not_found", message="فایل پیدا نشد.")
        return path
