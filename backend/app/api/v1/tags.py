from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.tag import Tag
from app.models.audio_file import AudioFile
from app.schemas.tag import (
    TagResponse,
    TagCreate,
    TagListResponse,
    AudioFileTagsUpdate
)
from app.api.deps import get_current_user
from app.auth.permissions import ensure_file_access

router = APIRouter()


@router.get("/", response_model=TagListResponse)
def list_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    タグ一覧を取得

    - **skip**: スキップする件数（デフォルト: 0）
    - **limit**: 取得する最大件数（デフォルト: 100）
    """
    query = db.query(Tag).order_by(Tag.name)
    total = query.count()
    tags = query.offset(skip).limit(limit).all()

    return TagListResponse(
        total=total,
        tags=[TagResponse.model_validate(t) for t in tags]
    )


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    新しいタグを作成

    - **name**: タグ名（必須、ユニーク）
    """
    # 既存のタグを確認
    existing_tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists"
        )

    tag = Tag(name=tag_data.name)
    db.add(tag)

    try:
        db.commit()
        db.refresh(tag)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists"
        )

    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    タグを削除

    - **tag_id**: タグID
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    db.delete(tag)
    db.commit()

    return None


@router.put("/{file_id}/tags", response_model=List[TagResponse])
def update_file_tags(
    file_id: int,
    tags_update: AudioFileTagsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ファイルのタグを更新（既存のタグを置き換え）

    - **file_id**: ファイルID
    - **tag_ids**: タグIDのリスト
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    # タグの存在確認
    tags = db.query(Tag).filter(Tag.id.in_(tags_update.tag_ids)).all()
    if len(tags) != len(tags_update.tag_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more tags not found"
        )

    # タグを更新
    audio_file.tags = tags
    db.commit()
    db.refresh(audio_file)

    return [TagResponse.model_validate(t) for t in audio_file.tags]


@router.post("/{file_id}/tags/{tag_id}", response_model=List[TagResponse])
def add_tag_to_file(
    file_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ファイルにタグを追加

    - **file_id**: ファイルID
    - **tag_id**: タグID
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    # タグが既に追加されていないかチェック
    if tag in audio_file.tags:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already added to this file"
        )

    audio_file.tags.append(tag)
    db.commit()
    db.refresh(audio_file)

    return [TagResponse.model_validate(t) for t in audio_file.tags]


@router.delete("/{file_id}/tags/{tag_id}", response_model=List[TagResponse])
def remove_tag_from_file(
    file_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ファイルからタグを削除

    - **file_id**: ファイルID
    - **tag_id**: タグID
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    # タグが追加されているかチェック
    if tag not in audio_file.tags:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag not found on this file"
        )

    audio_file.tags.remove(tag)
    db.commit()
    db.refresh(audio_file)

    return [TagResponse.model_validate(t) for t in audio_file.tags]
