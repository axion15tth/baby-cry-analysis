from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
import os
import shutil
import librosa
import soundfile as sf

from app.database import get_db
from app.models.user import User
from app.models.audio_file import AudioFile
from app.schemas.audio_file import (
    AudioFileResponse,
    AudioFileListResponse,
    AudioFileUploadResponse,
    AudioFileUpdate
)
from app.api.deps import get_current_user
from app.auth.permissions import check_researcher, ensure_file_access
from app.config import settings

router = APIRouter()


def extract_audio_metadata(file_path: str) -> tuple[Optional[int], Optional[float]]:
    """
    音声ファイルからメタデータ（サンプルレート、継続時間）を抽出

    Args:
        file_path: 音声ファイルのパス

    Returns:
        tuple: (sample_rate, duration)
    """
    try:
        # soundfileでメタデータを取得（高速）
        info = sf.info(file_path)
        sample_rate = info.samplerate
        duration = info.duration
        return int(sample_rate), float(duration)
    except Exception as e:
        print(f"Warning: Failed to extract audio metadata from {file_path}: {str(e)}")
        return None, None


@router.post("/upload/batch", status_code=status.HTTP_201_CREATED)
async def upload_multiple_audio_files(
    files: List[UploadFile] = File(...),
    recording_start_times: Optional[List[str]] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    複数の音声ファイルを一括アップロード

    - **files**: 音声ファイルのリスト（必須）
    - **recording_start_times**: 各ファイルの録音開始時刻（ISO 8601形式、オプション）
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per batch upload"
        )

    uploaded_files = []
    errors = []

    for idx, file in enumerate(files):
        try:
            # ファイルサイズチェック
            content = await file.read()
            file_size = len(content)

            max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size:
                errors.append({
                    "filename": file.filename,
                    "error": f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
                })
                continue

            # ファイル形式チェック
            allowed_extensions = [".wav", ".mp3", ".flac", ".m4a", ".ogg"]
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                errors.append({
                    "filename": file.filename,
                    "error": f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
                })
                continue

            # UUIDでファイル名を生成
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(settings.STORAGE_PATH, "audio", unique_filename)

            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # ファイルを保存
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # 音声メタデータを抽出
            sample_rate, duration = extract_audio_metadata(file_path)

            # recording_start_timeをパース
            parsed_recording_start_time = None
            if recording_start_times and idx < len(recording_start_times):
                try:
                    parsed_recording_start_time = datetime.fromisoformat(
                        recording_start_times[idx].replace('Z', '+00:00')
                    )
                except ValueError:
                    pass  # 無効な時刻フォーマットは無視

            # データベースにレコード作成
            audio_file = AudioFile(
                user_id=current_user.id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                sample_rate=sample_rate,
                duration=duration,
                recording_start_time=parsed_recording_start_time,
                status="uploaded"
            )

            db.add(audio_file)
            db.commit()
            db.refresh(audio_file)

            uploaded_files.append(AudioFileResponse.model_validate(audio_file))

        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "message": f"Successfully uploaded {len(uploaded_files)} files",
        "files": uploaded_files,
        "errors": errors if errors else None
    }


@router.post("/upload", response_model=AudioFileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio_file(
    file: UploadFile = File(...),
    recording_start_time: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音声ファイルをアップロード

    - **file**: 音声ファイル（必須）
    - **recording_start_time**: 録音開始時刻（ISO 8601形式、オプション）
    """
    # ファイルサイズチェック
    file_size = 0
    content = await file.read()
    file_size = len(content)

    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # MB to bytes
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # ファイル形式チェック（音声ファイルのみ許可）
    allowed_extensions = [".wav", ".mp3", ".flac", ".m4a", ".ogg"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
        )

    # UUIDでファイル名を生成
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.STORAGE_PATH, "audio", unique_filename)

    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # ファイルを保存
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # 音声メタデータを抽出
    sample_rate, duration = extract_audio_metadata(file_path)

    # recording_start_timeをパース
    parsed_recording_start_time = None
    if recording_start_time:
        try:
            parsed_recording_start_time = datetime.fromisoformat(recording_start_time.replace('Z', '+00:00'))
        except ValueError:
            # ファイル削除してエラー
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recording_start_time format. Use ISO 8601 format (e.g., 2024-01-01T12:00:00Z)"
            )

    # データベースにレコード作成
    audio_file = AudioFile(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        sample_rate=sample_rate,
        duration=duration,
        recording_start_time=parsed_recording_start_time,
        status="uploaded"
    )

    db.add(audio_file)
    db.commit()
    db.refresh(audio_file)

    return AudioFileUploadResponse(
        message="File uploaded successfully",
        file=AudioFileResponse.model_validate(audio_file)
    )


@router.get("/", response_model=AudioFileListResponse)
def list_audio_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音声ファイル一覧を取得

    - 研究者: 全ユーザーのファイルを取得可能
    - 一般ユーザー: 自分のファイルのみ取得可能

    - **skip**: スキップする件数（デフォルト: 0）
    - **limit**: 取得する最大件数（デフォルト: 100）
    """
    # 研究者は全ファイル、一般ユーザーは自分のファイルのみ
    query = db.query(AudioFile)
    if not check_researcher(current_user):
        query = query.filter(AudioFile.user_id == current_user.id)

    files = query.order_by(AudioFile.uploaded_at.desc()).offset(skip).limit(limit).all()
    total = query.count()

    return AudioFileListResponse(
        total=total,
        files=[AudioFileResponse.model_validate(f) for f in files]
    )


@router.get("/{file_id}", response_model=AudioFileResponse)
def get_audio_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    指定されたIDの音声ファイル情報を取得

    - 研究者: 全ファイルにアクセス可能
    - 一般ユーザー: 自分のファイルのみアクセス可能

    - **file_id**: ファイルID
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    return AudioFileResponse.model_validate(audio_file)


@router.patch("/{file_id}", response_model=AudioFileResponse)
def update_audio_file(
    file_id: int,
    update_data: AudioFileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音声ファイル情報を更新

    - 研究者: 全ファイルを更新可能
    - 一般ユーザー: 自分のファイルのみ更新可能

    - **file_id**: ファイルID
    - **update_data**: 更新データ
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    # 更新
    if update_data.recording_start_time is not None:
        audio_file.recording_start_time = update_data.recording_start_time
    if update_data.status is not None:
        audio_file.status = update_data.status

    db.commit()
    db.refresh(audio_file)

    return AudioFileResponse.model_validate(audio_file)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audio_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音声ファイルを削除（ファイルとDBレコードの両方）

    - 研究者: 全ファイルを削除可能
    - 一般ユーザー: 自分のファイルのみ削除可能

    - **file_id**: ファイルID
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    # ファイルを削除
    try:
        if os.path.exists(audio_file.file_path):
            os.remove(audio_file.file_path)
    except Exception as e:
        # ファイル削除に失敗してもDBレコードは削除する
        print(f"Failed to delete file: {str(e)}")

    # DBレコード削除
    db.delete(audio_file)
    db.commit()

    return None


@router.get("/{file_id}/stream")
def stream_audio_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音声ファイルをストリーミング配信

    - 研究者: 全ファイルにアクセス可能
    - 一般ユーザー: 自分のファイルのみアクセス可能

    - **file_id**: ファイルID
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 権限チェック
    ensure_file_access(current_user, audio_file.user_id)

    # ファイルが存在するかチェック
    if not os.path.exists(audio_file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file does not exist on disk"
        )

    # ファイルの拡張子からMIMEタイプを決定
    file_ext = os.path.splitext(audio_file.file_path)[1].lower()
    media_type_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg"
    }
    media_type = media_type_map.get(file_ext, "audio/mpeg")

    # ファイルを返す
    return FileResponse(
        path=audio_file.file_path,
        media_type=media_type,
        filename=audio_file.original_filename
    )
