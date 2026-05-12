import json
import logging
import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


# 从配置读取允许的 MIME 类型（魔数校验保持不变）
ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1"],
    "image/png": [b"\x89\x50\x4e\x47"],
    "image/gif": [b"\x47\x49\x46\x38"],
    "image/webp": [b"\x52\x49\x46\x46"],
    "image/bmp": [b"\x42\x4d"],
}

# 仅保留配置中声明的类型
CONFIGURED_TYPES = {t.strip() for t in settings.ALLOWED_MIME_TYPES.split(",")}
ALLOWED_MIME_TYPES = {k: v for k, v in ALLOWED_MIME_TYPES.items() if k in CONFIGURED_TYPES}

TYPE_TO_SUBDIR = json.loads(settings.TYPE_TO_SUBDIR)


def validate_file_content(file: UploadFile) -> None:
    """校验 MIME 类型 + 文件头魔数"""
    mime = file.content_type
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {mime}")

    content = file.file.read(16)
    file.file.seek(0)

    valid_magic = ALLOWED_MIME_TYPES.get(mime, [])
    if not any(content.startswith(magic) for magic in valid_magic):
        raise HTTPException(status_code=400, detail="文件内容与声明类型不符")

    # webp 魔数前4字节是 RIFF...WEBN，需要更长的前导检测
    if mime == "image/webp":
        if not (content[:4] == b"RIFF" and content[8:12] == b"WEBP"):
            raise HTTPException(status_code=400, detail="文件内容与声明类型不符")


def validate_file_size(file: UploadFile, max_mb: int | None = None) -> None:
    """校验文件大小，max_mb 传 None 则用配置默认值"""
    if max_mb is None:
        max_mb = settings.UPLOAD_MAX_SIZE_MB

    file.file.seek(0, 2)  # seek to end
    size = file.file.tell()
    file.file.seek(0)

    if size > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件大小超过 {max_mb}MB 限制")


def get_extension(filename: str) -> str:
    """从原始文件名提取扩展名（不含点）"""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""


def save_uploaded_file(file: UploadFile, file_type: str) -> str:
    """保存文件到 uploads/{subdir}/，返回相对路径如 activities/uuid.jpg"""
    if file_type not in TYPE_TO_SUBDIR:
        raise HTTPException(status_code=400, detail="无效的 type 参数")

    subdir = TYPE_TO_SUBDIR[file_type]
    ext = get_extension(file.filename or "file")
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    upload_dir = Path("uploads") / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / filename
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    return f"{subdir}/{filename}"


def delete_activity_files(image_urls: list[str], qrcode_urls: list[str]) -> str:
    """删除活动关联的物理文件。失败只记警告日志，返回状态描述。"""
    total = len(image_urls) + len(qrcode_urls)
    if total == 0:
        return "无文件需清理"

    failed = 0
    for url in image_urls + qrcode_urls:
        if not url:
            continue
        # URL 格式：/uploads/activities/uuid.jpg → path: uploads/activities/uuid.jpg
        path_str = url.lstrip("/")
        file_path = Path(path_str)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("已删除物理文件: %s", path_str)
        except Exception:
            logger.warning("删除物理文件失败: %s", path_str, exc_info=True)
            failed += 1

    if failed == 0:
        return "文件已清理"
    return f"文件清理：{total - failed}/{total} 成功"
