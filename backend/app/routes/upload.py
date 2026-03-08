from fastapi import APIRouter, UploadFile, File, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.exceptions.business import BusinessError
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/upload", tags=["文件上传"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".txt", ".xlsx", ".xls"}
ALLOWED_MIMES = {
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg", "image/png", "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
CHUNK_SIZE = 8192


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传文件，返回文件 URL"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessError(1001, f"不支持的文件类型: {ext}")

    # 验证 MIME 类型
    if file.content_type not in ALLOWED_MIMES:
        raise BusinessError(1001, f"文件类型不匹配: {file.content_type}")

    # 按日期分目录存储
    date_dir = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(UPLOAD_DIR, date_dir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(save_dir, filename)

    # 流式写入，避免大文件占用内存
    size = 0
    try:
        with open(filepath, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise BusinessError(1001, "文件大小不能超过 10MB")
                f.write(chunk)
    except BusinessError:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise

    url = f"/uploads/{date_dir}/{filename}"
    return {"url": url, "filename": file.filename, "size": size}
