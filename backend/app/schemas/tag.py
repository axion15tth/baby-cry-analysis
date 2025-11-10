from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    total: int
    tags: List[TagResponse]


class AudioFileTagsUpdate(BaseModel):
    tag_ids: List[int]
