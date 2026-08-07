import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import invalid_operation, resource_not_found
from app.models.base import utc_now
from app.models.collaboration import Attachment, Checklist, ChecklistItem, Comment
from app.models.identity import User
from app.models.task import TaskAssignee
from app.models.workspace import ActivityLog, Notification, WorkspaceMember
from app.repositories.collaboration import (
    ActivityRepository,
    AttachmentRepository,
    ChecklistRepository,
    CommentRepository,
)
from app.services.task import TaskService
from app.storage.local import LocalStorageService


class CollaborationService:
    def __init__(self, session: AsyncSession, storage: LocalStorageService) -> None:
        self.session = session
        self.comments = CommentRepository(session)
        self.checklists = ChecklistRepository(session)
        self.attachments = AttachmentRepository(session)
        self.activity = ActivityRepository(session)
        self.tasks = TaskService(session)
        self.storage = storage

    async def create_comment(self, actor: User, task_id: UUID, *, body: str) -> Comment:
        async with self.session.begin():
            task = await self.tasks._required_task(task_id)
            project, _ = await self.tasks._access(actor, task.project_id)
            comment = await self.comments.add(
                Comment(
                    task_id=task_id,
                    author_id=actor.id,
                    body=body,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
            )
            await self._activity(task_id, actor, "task.comment_created")
            assignees = await self.session.scalars(
                select(TaskAssignee.user_id).where(TaskAssignee.task_id == task_id)
            )
            for user_id in assignees:
                if user_id != actor.id:
                    self.session.add(
                        Notification(
                            user_id=user_id,
                            type="task.comment",
                            title="نظر جدید روی وظیفه",
                            body=None,
                            entity_type="task",
                            entity_id=task_id,
                            action_url=f"/app/tasks/{task_id}",
                            dedupe_key=f"task.comment:{comment.id}:{user_id}",
                            created_at=utc_now(),
                        )
                    )
            mentioned = {
                item.lower()
                for item in re.findall(r"@([\w.+-]+@[\w.-]+)", body, flags=re.IGNORECASE)
            }
            if mentioned:
                members = await self.session.execute(
                    select(User.id, User.email)
                    .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
                    .where(WorkspaceMember.workspace_id == project.workspace_id)
                )
                for user_id, email in members:
                    if user_id != actor.id and email.lower() in mentioned:
                        self.session.add(
                            Notification(
                                user_id=user_id,
                                type="task.mention",
                                title="در یک نظر از شما نام برده شد",
                                body=None,
                                entity_type="task",
                                entity_id=task_id,
                                action_url=f"/app/tasks/{task_id}",
                                dedupe_key=f"task.mention:{comment.id}:{user_id}",
                                created_at=utc_now(),
                            )
                        )
            await self.session.flush()
            return comment

    async def create_checklist(self, actor: User, task_id: UUID, *, title: str) -> Checklist:
        async with self.session.begin():
            task = await self.tasks._required_task(task_id)
            await self.tasks._mutate(actor, task.project_id)
            checklist = await self.checklists.add(
                Checklist(
                    task_id=task.id,
                    title=title,
                    position=await self.checklists.next_position(task.id),
                )
            )
            await self._activity(task.id, actor, "task.checklist_created")
            return checklist

    async def create_checklist_item(
        self, actor: User, checklist_id: UUID, *, title: str, completed: bool
    ) -> ChecklistItem:
        async with self.session.begin():
            checklist = await self.checklists.get(checklist_id)
            if checklist is None:
                raise resource_not_found()
            task = await self.tasks._required_task(checklist.task_id)
            await self.tasks._mutate(actor, task.project_id)
            item = await self.checklists.add_item(
                ChecklistItem(
                    checklist_id=checklist.id,
                    title=title,
                    completed=completed,
                    position=await self.checklists.next_item_position(checklist.id),
                )
            )
            await self._activity(task.id, actor, "task.checklist_item_created")
            return item

    async def list_checklists(
        self, actor: User, task_id: UUID
    ) -> list[tuple[Checklist, list[ChecklistItem]]]:
        async with self.session.begin():
            task = await self.tasks._required_task(task_id)
            await self.tasks._access(actor, task.project_id)
            checklists = await self.checklists.list_for_task(task.id)
            return [(item, await self.checklists.list_items(item.id)) for item in checklists]

    async def update_checklist(self, actor: User, checklist_id: UUID, *, title: str) -> Checklist:
        async with self.session.begin():
            checklist = await self._required_checklist(checklist_id)
            task = await self.tasks._required_task(checklist.task_id)
            await self.tasks._mutate(actor, task.project_id)
            checklist.title = title
            await self.session.flush()
            await self._activity(task.id, actor, "task.checklist_updated")
            return checklist

    async def delete_checklist(self, actor: User, checklist_id: UUID) -> None:
        async with self.session.begin():
            checklist = await self._required_checklist(checklist_id)
            task = await self.tasks._required_task(checklist.task_id)
            await self.tasks._mutate(actor, task.project_id)
            await self.session.delete(checklist)
            await self.session.flush()
            await self._activity(task.id, actor, "task.checklist_deleted")

    async def update_checklist_item(
        self, actor: User, item_id: UUID, *, title: str | None, completed: bool | None
    ) -> ChecklistItem:
        async with self.session.begin():
            item = await self.checklists.get_item(item_id)
            if item is None:
                raise resource_not_found()
            checklist = await self.checklists.get(item.checklist_id)
            if checklist is None:
                raise resource_not_found()
            task = await self.tasks._required_task(checklist.task_id)
            await self.tasks._mutate(actor, task.project_id)
            if title is not None:
                item.title = title
            if completed is not None:
                item.completed = completed
            await self.session.flush()
            await self._activity(task.id, actor, "task.checklist_item_updated")
            return item

    async def delete_checklist_item(self, actor: User, item_id: UUID) -> None:
        async with self.session.begin():
            item = await self._required_item(item_id)
            checklist = await self._required_checklist(item.checklist_id)
            task = await self.tasks._required_task(checklist.task_id)
            await self.tasks._mutate(actor, task.project_id)
            await self.session.delete(item)
            await self.session.flush()
            await self._activity(task.id, actor, "task.checklist_item_deleted")

    async def reorder_checklist_items(
        self, actor: User, checklist_id: UUID, *, item_ids: list[UUID]
    ) -> list[ChecklistItem]:
        async with self.session.begin():
            checklist = await self._required_checklist(checklist_id)
            task = await self.tasks._required_task(checklist.task_id)
            await self.tasks._mutate(actor, task.project_id)
            items = await self.checklists.list_items(checklist.id)
            by_id = {item.id: item for item in items}
            if len(item_ids) != len(by_id) or set(item_ids) != set(by_id):
                raise invalid_operation("فهرست آیتم‌ها باید کامل و یکتا باشد.")  # noqa: RUF001
            for position, item_id in enumerate(item_ids):
                by_id[item_id].position = position
            await self.session.flush()
            await self._activity(task.id, actor, "task.checklist_items_reordered")
            return [by_id[item_id] for item_id in item_ids]

    async def list_comments(
        self, actor: User, task_id: UUID, *, page: int, page_size: int
    ) -> tuple[list[Comment], int]:
        async with self.session.begin():
            await self.tasks._access(actor, (await self.tasks._required_task(task_id)).project_id)
            return await self.comments.list(task_id, page=page, page_size=page_size)

    async def update_comment(self, actor: User, comment_id: UUID, *, body: str) -> Comment:
        async with self.session.begin():
            comment = await self._required_comment(comment_id)
            task = await self.tasks._required_task(comment.task_id)
            await self.tasks._access(actor, task.project_id)
            if comment.author_id != actor.id:
                await self.tasks._mutate(actor, task.project_id)
            comment.body = body
            comment.updated_at = utc_now()
            await self.session.flush()
            await self._activity(task.id, actor, "task.comment_updated")
            return comment

    async def delete_comment(self, actor: User, comment_id: UUID) -> None:
        async with self.session.begin():
            comment = await self._required_comment(comment_id)
            task = await self.tasks._required_task(comment.task_id)
            await self.tasks._access(actor, task.project_id)
            if comment.author_id != actor.id:
                await self.tasks._mutate(actor, task.project_id)
            await self.session.delete(comment)
            await self.session.flush()
            await self._activity(task.id, actor, "task.comment_deleted")

    async def upload_attachment(
        self, actor: User, task_id: UUID, *, original_name: str, content_type: str, data: bytes
    ) -> Attachment:
        storage_name = self.storage.save(
            original_name=original_name, content_type=content_type, data=data
        )
        try:
            async with self.session.begin():
                task = await self.tasks._required_task(task_id)
                await self.tasks._mutate(actor, task.project_id)
                attachment = await self.attachments.add(
                    Attachment(
                        task_id=task.id,
                        uploaded_by_id=actor.id,
                        original_name=original_name,
                        storage_name=storage_name,
                        content_type=content_type,
                        size_bytes=len(data),
                    )
                )
                await self._activity(task.id, actor, "task.attachment_uploaded")
                return attachment
        except Exception:
            self.storage.delete(storage_name)
            raise

    async def list_attachments(self, actor: User, task_id: UUID) -> list[Attachment]:
        async with self.session.begin():
            task = await self.tasks._required_task(task_id)
            await self.tasks._access(actor, task.project_id)
            return await self.attachments.list(task.id)

    async def download_attachment(
        self, actor: User, attachment_id: UUID
    ) -> tuple[Attachment, bytes]:
        async with self.session.begin():
            attachment = await self._required_attachment(attachment_id)
            task = await self.tasks._required_task(attachment.task_id)
            await self.tasks._access(actor, task.project_id)
            return attachment, self.storage.read(attachment.storage_name)

    async def delete_attachment(self, actor: User, attachment_id: UUID) -> None:
        async with self.session.begin():
            attachment = await self._required_attachment(attachment_id)
            task = await self.tasks._required_task(attachment.task_id)
            await self.tasks._mutate(actor, task.project_id)
            storage_name = attachment.storage_name
            await self.session.delete(attachment)
            await self.session.flush()
            await self._activity(task.id, actor, "task.attachment_deleted")
        self.storage.delete(storage_name)

    async def list_activity(self, actor: User, task_id: UUID) -> list[ActivityLog]:
        async with self.session.begin():
            task = await self.tasks._required_task(task_id)
            await self.tasks._access(actor, task.project_id)
            return await self.activity.list_task(task.id, limit=100)

    async def _required_comment(self, comment_id: UUID) -> Comment:
        comment = await self.comments.get(comment_id)
        if comment is None:
            raise resource_not_found()
        return comment

    async def _required_checklist(self, checklist_id: UUID) -> Checklist:
        checklist = await self.checklists.get(checklist_id)
        if checklist is None:
            raise resource_not_found()
        return checklist

    async def _required_item(self, item_id: UUID) -> ChecklistItem:
        item = await self.checklists.get_item(item_id)
        if item is None:
            raise resource_not_found()
        return item

    async def _required_attachment(self, attachment_id: UUID) -> Attachment:
        attachment = await self.attachments.get(attachment_id)
        if attachment is None:
            raise resource_not_found()
        return attachment

    async def _activity(self, task_id: UUID, actor: User, action: str) -> None:
        project, _ = await self.tasks._access(
            actor, (await self.tasks._required_task(task_id)).project_id
        )
        await self.activity.add(
            ActivityLog(
                workspace_id=project.workspace_id,
                actor_id=actor.id,
                entity_type="task",
                entity_id=task_id,
                action=action,
                details={},
                created_at=utc_now(),
            )
        )
