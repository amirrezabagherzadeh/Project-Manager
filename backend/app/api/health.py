from fastapi import APIRouter

from app.schemas.common import HealthData, HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="بررسی سلامت سرویس",
    description="آمادگی API برای دریافت درخواست را بدون افشای تنظیمات محیط گزارش می‌کند.",
    response_model=HealthResponse,
    status_code=200,
    responses={
        200: {
            "description": "سرویس آماده است.",
            "content": {
                "application/json": {
                    "example": {"data": {"status": "ok"}},
                }
            },
        }
    },
)
async def health() -> HealthResponse:
    return HealthResponse(data=HealthData(status="ok"))
