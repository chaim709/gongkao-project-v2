"""导入指定Excel文件"""
import asyncio
import sys
from app.database import AsyncSessionLocal
from app.services.position_import_service import PositionImportService


async def import_file(file_path: str):
    """导入Excel文件"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        async with AsyncSessionLocal() as db:
            result = await PositionImportService.import_positions(db, content)
            print(f"✅ 导入完成")
            print(f"成功: {result['success_count']} 条")
            print(f"失败: {result['error_count']} 条")
            if result['errors']:
                print(f"\n错误信息:")
                for err in result['errors']:
                    print(f"  - {err}")
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 import_file.py <excel文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    asyncio.run(import_file(file_path))
