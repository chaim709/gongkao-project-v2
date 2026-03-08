"""清空岗位数据脚本"""
import asyncio
from sqlalchemy import delete
from app.database import AsyncSessionLocal
from app.models.position import Position


async def clear_positions():
    """清空所有岗位数据"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(delete(Position))
        await db.commit()
        print(f"已删除 {result.rowcount} 条岗位数据")


if __name__ == "__main__":
    asyncio.run(clear_positions())
