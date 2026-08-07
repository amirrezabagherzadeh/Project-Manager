from typing import Any


class DomainError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def resource_conflict(message: str = "این مورد از قبل وجود دارد.") -> DomainError:
    return DomainError(
        status_code=409,
        code="resource_conflict",
        message=message,
    )


def invalid_credentials() -> DomainError:
    return DomainError(
        status_code=401,
        code="invalid_credentials",
        message="ایمیل یا رمز عبور صحیح نیست.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def authentication_required() -> DomainError:
    return DomainError(
        status_code=401,
        code="authentication_required",
        message="برای ادامه وارد حساب شوید.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def token_expired() -> DomainError:
    return DomainError(
        status_code=401,
        code="token_expired",
        message="نشست شما منقضی شده است. دوباره وارد شوید.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def permission_denied() -> DomainError:
    return DomainError(
        status_code=403,
        code="permission_denied",
        message="اجازه انجام این عملیات را ندارید.",
    )


def resource_not_found(message: str = "منبع مورد نظر پیدا نشد.") -> DomainError:
    return DomainError(
        status_code=404,
        code="resource_not_found",
        message=message,
    )


def invalid_operation(message: str = "انجام این عملیات مجاز نیست.") -> DomainError:
    return DomainError(
        status_code=409,
        code="invalid_operation",
        message=message,
    )


def version_conflict() -> DomainError:
    return DomainError(
        status_code=409,
        code="version_conflict",
        message="وظیفه تغییر کرده است. داده را تازه‌سازی کنید.",
    )


def rate_limited(retry_after_seconds: int) -> DomainError:
    return DomainError(
        status_code=429,
        code="rate_limited",
        message="درخواست‌های زیادی ارسال شده است. کمی بعد تلاش کنید.",
        details={"retry_after_seconds": retry_after_seconds},
        headers={"Retry-After": str(retry_after_seconds)},
    )
