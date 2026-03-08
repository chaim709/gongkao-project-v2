from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditService:
    async def log(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int = None,
        old_value: dict = None,
        new_value: dict = None,
        ip_address: str = None,
    ):
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        db.add(audit)
        await db.flush()


audit_service = AuditService()
