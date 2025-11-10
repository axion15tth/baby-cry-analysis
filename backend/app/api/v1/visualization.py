from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.audio_file import AudioFile
from app.models.analysis_result import AnalysisResult
from app.api.deps import get_current_user
from app.visualization.waveform_generator import WaveformGenerator
from app.visualization.spectrogram_generator import SpectrogramGenerator

router = APIRouter()


@router.get("/waveform/{file_id}")
def get_waveform_data(
    file_id: int,
    episode_id: Optional[str] = Query(None, description="エピソードID（例: episode_0）。指定しない場合はファイル全体"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    波形データを取得

    - **file_id**: 音声ファイルID
    - **episode_id**: エピソードID（オプション）

    Returns:
        - time: 時間軸データ（秒）
        - amplitude: 振幅データ
        - sample_rate: サンプリングレート
    """
    # ファイルの取得
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 解析結果を取得（エピソード情報のため）
    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).first()

    # 波形データ生成
    generator = WaveformGenerator()

    if episode_id and analysis_result:
        # 特定エピソードの波形
        cry_episodes = analysis_result.result_data.get("cry_episodes", [])
        episode_index = int(episode_id.split("_")[1])

        if episode_index >= len(cry_episodes):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        episode = cry_episodes[episode_index]
        waveform_data = generator.generate_episode_waveform(
            audio_file.file_path,
            episode["start_time"],
            episode["end_time"]
        )
    else:
        # ファイル全体の波形
        waveform_data = generator.generate_full_waveform(audio_file.file_path)

    return waveform_data


@router.get("/spectrogram/{file_id}")
def get_spectrogram_data(
    file_id: int,
    episode_id: Optional[str] = Query(None, description="エピソードID（例: episode_0）。指定しない場合はファイル全体"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    スペクトログラムデータを取得

    - **file_id**: 音声ファイルID
    - **episode_id**: エピソードID（オプション）

    Returns:
        - times: 時間軸データ（秒）
        - frequencies: 周波数軸データ（Hz）
        - spectrogram: スペクトログラムデータ（2次元配列、dB単位）
    """
    # ファイルの取得
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == file_id,
        AudioFile.user_id == current_user.id
    ).first()

    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    # 解析結果を取得（エピソード情報のため）
    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.audio_file_id == file_id
    ).first()

    # スペクトログラムデータ生成
    generator = SpectrogramGenerator()

    if episode_id and analysis_result:
        # 特定エピソードのスペクトログラム
        cry_episodes = analysis_result.result_data.get("cry_episodes", [])
        episode_index = int(episode_id.split("_")[1])

        if episode_index >= len(cry_episodes):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode {episode_id} not found"
            )

        episode = cry_episodes[episode_index]
        spectrogram_data = generator.generate_episode_spectrogram(
            audio_file.file_path,
            episode["start_time"],
            episode["end_time"]
        )
    else:
        # ファイル全体のスペクトログラム
        spectrogram_data = generator.generate_full_spectrogram(audio_file.file_path)

    return spectrogram_data
