from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.audio_file import AudioFile
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.deps import get_current_user
from app.auth.permissions import check_researcher
from app.utils.security import get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザー一覧を取得（研究者のみ）

    - **skip**: スキップする件数
    - **limit**: 取得する最大件数
    - **search**: メールアドレスで検索（部分一致）
    - **role**: ロールでフィルター（user / researcher）
    """
    # 研究者権限チェック
    if not check_researcher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能は研究者アカウントのみ利用可能です"
        )

    query = db.query(User)

    # 検索フィルター
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))

    # ロールフィルター
    if role:
        query = query.filter(User.role == role)

    # 取得
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    指定されたIDのユーザー情報を取得（研究者のみ）

    - **user_id**: ユーザーID
    """
    # 研究者権限チェック
    if not check_researcher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能は研究者アカウントのみ利用可能です"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    新しいユーザーを作成（研究者のみ）

    - **email**: メールアドレス
    - **password**: パスワード
    - **role**: ロール（user / researcher）
    """
    # 研究者権限チェック
    if not check_researcher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能は研究者アカウントのみ利用可能です"
        )

    # メール重複チェック
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # ユーザー作成
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザー情報を更新（研究者のみ）

    - **user_id**: ユーザーID
    - **email**: 新しいメールアドレス（オプション）
    """
    # 研究者権限チェック
    if not check_researcher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能は研究者アカウントのみ利用可能です"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # メールアドレスの更新
    if update_data.email:
        # 重複チェック（自分以外）
        existing_user = db.query(User).filter(
            User.email == update_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = update_data.email

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ユーザーを削除（研究者のみ）

    - **user_id**: ユーザーID

    注意: ユーザーに紐づくファイルも全て削除されます
    """
    # 研究者権限チェック
    if not check_researcher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能は研究者アカウントのみ利用可能です"
        )

    # 自分自身は削除できない
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # ユーザーに紐づくファイルを削除
    audio_files = db.query(AudioFile).filter(AudioFile.user_id == user_id).all()
    for audio_file in audio_files:
        # ファイルシステムから削除
        import os
        if os.path.exists(audio_file.file_path):
            try:
                os.remove(audio_file.file_path)
            except Exception as e:
                print(f"Failed to delete file: {str(e)}")

    # DBレコード削除（cascadeで関連レコードも削除される）
    db.delete(user)
    db.commit()

    return None


@router.get("/{user_id}/files", response_model=List[dict])
def get_user_files(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    指定されたユーザーのファイル一覧を取得（研究者のみ）

    - **user_id**: ユーザーID
    """
    # 研究者権限チェック
    if not check_researcher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能は研究者アカウントのみ利用可能です"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    audio_files = db.query(AudioFile).filter(AudioFile.user_id == user_id).order_by(AudioFile.uploaded_at.desc()).all()

    return [
        {
            "id": f.id,
            "original_filename": f.original_filename,
            "file_size": f.file_size,
            "status": f.status,
            "uploaded_at": f.uploaded_at
        }
        for f in audio_files
    ]
