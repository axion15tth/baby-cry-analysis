from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.database import get_db
from app.models.user import User
from app.models.audio_file import AudioFile
from app.models.analysis_result import AnalysisResult
from app.api.deps import get_current_user
from app.export.csv_exporter import CSVExporter
from app.export.excel_exporter import ExcelExporter
from app.export.pdf_exporter import PDFExporter

router = APIRouter()


@router.get("/csv/episodes/{file_id}")
def export_episodes_csv(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    泣き声エピソードをCSV形式でエクスポート

    - **file_id**: 音声ファイルID
    """
    # ファイルと解析結果を取得
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).first()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )

    # CSV生成
    exporter = CSVExporter()
    csv_data = exporter.export_cry_episodes(
        analysis_result.result_data,
        audio_file.recording_start_time
    )

    # レスポンス
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=cry_episodes_{file_id}.csv"
        }
    )


@router.get("/csv/features/{file_id}/{episode_id}")
def export_features_csv(
    file_id: int,
    episode_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    音響特徴をCSV形式でエクスポート

    - **file_id**: 音声ファイルID
    - **episode_id**: エピソードID（例: episode_0）
    """
    # ファイルと解析結果を取得
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).first()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )

    # エピソードIDの検証
    if episode_id not in analysis_result.result_data.get("acoustic_features", {}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found"
        )

    # CSV生成
    exporter = CSVExporter()
    csv_data = exporter.export_acoustic_features(
        analysis_result.result_data,
        episode_id,
        audio_file.recording_start_time
    )

    # レスポンス
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=acoustic_features_{file_id}_{episode_id}.csv"
        }
    )


@router.get("/excel/{file_id}")
def export_excel(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解析結果をExcel形式でエクスポート（4シート構成）

    - **file_id**: 音声ファイルID

    シート構成:
    1. 概要 - ファイル情報と解析サマリー
    2. 泣き声エピソード - 検出されたエピソード一覧
    3. 音響特徴統計 - 各エピソードの統計情報と特殊パラメータ
    4. 音響特徴 - 時系列の音響特徴データ
    """
    # ファイルと解析結果を取得
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).first()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )

    # ファイル情報を準備
    file_info = {
        "original_filename": audio_file.original_filename,
        "file_size": audio_file.file_size,
        "analyzed_at": analysis_result.analyzed_at.strftime("%Y-%m-%d %H:%M:%S") if analysis_result.analyzed_at else ""
    }

    # Excel生成
    exporter = ExcelExporter()
    excel_data = exporter.export(
        analysis_result.result_data,
        file_info,
        audio_file.recording_start_time
    )

    # レスポンス
    return StreamingResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=analysis_report_{file_id}.xlsx"
        }
    )


@router.get("/pdf/{file_id}")
def export_pdf(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解析結果をPDF形式でエクスポート

    - **file_id**: 音声ファイルID
    """
    # ファイルと解析結果を取得
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).first()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis result not found"
        )

    # ファイル情報を準備
    file_info = {
        "original_filename": audio_file.original_filename,
        "file_size": audio_file.file_size,
        "analyzed_at": analysis_result.analyzed_at.strftime("%Y-%m-%d %H:%M:%S") if analysis_result.analyzed_at else ""
    }

    # PDF生成
    exporter = PDFExporter()
    pdf_data = exporter.export(
        analysis_result.result_data,
        file_info,
        audio_file.recording_start_time
    )

    # レスポンス
    return StreamingResponse(
        BytesIO(pdf_data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=analysis_report_{file_id}.pdf"
        }
    )
