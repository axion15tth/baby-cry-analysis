from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.audio_file import AudioFile
from app.models.analysis_result import AnalysisResult
from app.schemas.analysis_result import (
    AnalysisRequestSchema,
    AnalysisStatusSchema,
    AnalysisResultResponse
)
from app.api.deps import get_current_user
from app.tasks.analysis_tasks import analyze_audio_file
from celery.result import AsyncResult
from app.celery_app import celery_app

router = APIRouter()


@router.post("/start", response_model=AnalysisStatusSchema, status_code=status.HTTP_202_ACCEPTED)
def start_analysis(
    request: AnalysisRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音声ファイルの解析を開始

    - **file_id**: 解析する音声ファイルのID
    """
    # ファイルの存在確認と権限チェック
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == request.file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # すでに処理中または完了している場合はエラー
    if audio_file.status in ["processing", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is already {audio_file.status}"
        )

    # Celeryタスクを開始
    task = analyze_audio_file.delay(request.file_id)

    # タスクIDをデータベースに保存
    audio_file.task_id = task.id
    db.commit()

    return AnalysisStatusSchema(
        file_id=request.file_id,
        status="processing",
        message="Analysis started",
        progress=0,
        task_id=task.id
    )


@router.get("/status/{file_id}", response_model=AnalysisStatusSchema)
def get_analysis_status(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解析のステータスを取得

    - **file_id**: 音声ファイルID
    """
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    status_messages = {
        "uploaded": "File uploaded, analysis not started",
        "processing": "Analysis in progress",
        "completed": "Analysis completed",
        "failed": "Analysis failed"
    }

    progress = None
    task_id = audio_file.task_id

    # 処理中の場合、タスクの進捗を取得
    if audio_file.status == "processing" and audio_file.task_id:
        try:
            task_result = AsyncResult(audio_file.task_id, app=celery_app)
            if task_result.state == 'PROGRESS':
                task_info = task_result.info
                if isinstance(task_info, dict):
                    progress = task_info.get('progress', 0)
                    message = task_info.get('message', status_messages.get(audio_file.status))
                else:
                    message = status_messages.get(audio_file.status)
            else:
                message = status_messages.get(audio_file.status)
        except Exception:
            message = status_messages.get(audio_file.status)
    else:
        message = status_messages.get(audio_file.status, "Unknown status")
        if audio_file.status == "completed":
            progress = 100

    return AnalysisStatusSchema(
        file_id=file_id,
        status=audio_file.status,
        message=message,
        progress=progress,
        task_id=task_id
    )


@router.get("/results/{file_id}", response_model=List[AnalysisResultResponse])
def get_analysis_results(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解析結果を取得

    - **file_id**: 音声ファイルID
    """
    # ファイルの存在確認と権限チェック
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 解析結果を取得
    results = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).all()

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis results found for this file"
        )

    return [AnalysisResultResponse.model_validate(result) for result in results]
