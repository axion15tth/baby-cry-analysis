from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.tag import TagResponse


class AudioFileBase(BaseModel):
    """AudioFileの基本スキーマ"""
    original_filename: str
    recording_start_time: Optional[datetime] = None


class AudioFileCreate(AudioFileBase):
    """AudioFile作成時のスキーマ"""
    pass


class AudioFileUpdate(BaseModel):
    """AudioFile更新時のスキーマ"""
    recording_start_time: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(uploaded|processing|completed|failed)$")


class AudioFileResponse(AudioFileBase):
    """AudioFileレスポンススキーマ"""
    id: int
    user_id: int
    filename: str
    file_path: str
    file_size: int
    sample_rate: Optional[int] = None
    duration: Optional[float] = None
    status: str
    uploaded_at: datetime
    tags: List['TagResponse'] = []

    class Config:
        from_attributes = True


class AudioFileListResponse(BaseModel):
    """AudioFileリストレスポンススキーマ"""
    total: int
    files: list[AudioFileResponse]


class AudioFileUploadResponse(BaseModel):
    """ファイルアップロード成功レスポンス"""
    message: str
    file: AudioFileResponse


# Forward reference resolution
from app.schemas.tag import TagResponse  # noqa: E402
AudioFileResponse.model_rebuild()
