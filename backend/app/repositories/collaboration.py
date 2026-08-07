from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collaboration import Attachment, Checklist, ChecklistItem, Comment
from app.models.workspace import ActivityLog


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get(self, comment_id: UUID) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def list(self, task_id: UUID, *, page: int, page_size: int) -> tuple[list[Comment], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(Comment).where(Comment.task_id == task_id)
        )
        rows = await self.session.scalars(
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at, Comment.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows), int(total or 0)


class ChecklistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, checklist: Checklist) -> Checklist:
        self.session.add(checklist)
        await self.session.flush()
        return checklist

    async def add_item(self, item: ChecklistItem) -> ChecklistItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, checklist_id: UUID) -> Checklist | None:
        return await self.session.get(Checklist, checklist_id)

    async def get_item(self, item_id: UUID) -> ChecklistItem | None:
        return await self.session.get(ChecklistItem, item_id)

    async def list_for_task(self, task_id: UUID) -> list[Checklist]:
        return list(
            await self.session.scalars(
                select(Checklist).where(Checklist.task_id == task_id).order_by(Checklist.position)
            )
        )

    async def list_items(self, checklist_id: UUID) -> list[ChecklistItem]:
        return list(
            await self.session.scalars(
                select(ChecklistItem)
                .where(ChecklistItem.checklist_id == checklist_id)
                .order_by(ChecklistItem.position)
            )
        )

    async def next_position(self, task_id: UUID) -> int:
        value = await self.session.scalar(
            select(func.max(Checklist.position)).where(Checklist.task_id == task_id)
        )
        return int(value) + 1 if value is not None else 0

    async def next_item_position(self, checklist_id: UUID) -> int:
        value = await self.session.scalar(
            select(func.max(ChecklistItem.position)).where(
                ChecklistItem.checklist_id == checklist_id
            )
        )
        return int(value) + 1 if value is not None else 0


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.flush()
        return attachment

    async def get(self, attachment_id: UUID) -> Attachment | None:
        return await self.session.get(Attachment, attachment_id)

    async def list(self, task_id: UUID) -> list[Attachment]:
        return list(
            await self.session.scalars(
                select(Attachment)
                .where(Attachment.task_id == task_id)
                .order_by(Attachment.created_at.desc(), Attachment.id)
            )
        )


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: ActivityLog) -> ActivityLog:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_task(self, task_id: UUID, *, limit: int) -> list[ActivityLog]:
        return list(
            await self.session.scalars(
                select(ActivityLog)
                .where(ActivityLog.entity_type == "task", ActivityLog.entity_id == task_id)
                .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
                .limit(limit)
            )
        )
