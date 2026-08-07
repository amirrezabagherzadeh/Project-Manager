from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.collaboration import router as collaboration_router
from app.api.v1.endpoints.notifications import router as notification_router
from app.api.v1.endpoints.projects import router as project_router
from app.api.v1.endpoints.reporting import router as reporting_router
from app.api.v1.endpoints.tasks import router as task_router
from app.api.v1.endpoints.workspaces import router as workspace_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(workspace_router)
router.include_router(project_router)
router.include_router(task_router)
router.include_router(collaboration_router)
router.include_router(notification_router)
router.include_router(reporting_router)
