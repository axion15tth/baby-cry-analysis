from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, List, Optional


class AnalysisResultBase(BaseModel):
    """AnalysisResultの基本スキーマ"""
    result_data: Dict[str, Any]


class AnalysisResultCreate(AnalysisResultBase):
    """AnalysisResult作成時のスキーマ"""
    audio_file_id: int


class AnalysisResultResponse(AnalysisResultBase):
    """AnalysisResultレスポンススキーマ"""
    id: int
    audio_file_id: int
    analyzed_at: datetime

    class Config:
        from_attributes = True


class CryEpisodeSchema(BaseModel):
    """泣き声エピソードスキーマ"""
    start_time: float
    end_time: float
    duration: float
    confidence: float


class AcousticFeaturesSchema(BaseModel):
    """音響特徴スキーマ"""
    time: float
    f0: Optional[float] = None
    f1: Optional[float] = None
    f2: Optional[float] = None
    f3: Optional[float] = None
    hnr: Optional[float] = None
    shimmer: Optional[float] = None
    jitter: Optional[float] = None
    intensity: Optional[float] = None


class StatisticsSchema(BaseModel):
    """統計量スキーマ"""
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None


class AnalysisParametersSchema(BaseModel):
    """解析パラメータのカスタマイズ設定"""

    high_pitch_threshold: Optional[float] = Field(
        default=500.0,
        description="High-pitch判定の閾値（Hz）",
        ge=100.0,
        le=2000.0
    )

    hyper_phonation_threshold: Optional[float] = Field(
        default=30.0,
        description="Hyper-phonation判定のHNR閾値（dB）",
        ge=10.0,
        le=50.0
    )

    noise_reduction_level: Optional[int] = Field(
        default=1,
        description="ノイズ除去レベル（0=なし、1=弱、2=中、3=強）",
        ge=0,
        le=3
    )

    min_cry_duration: Optional[float] = Field(
        default=0.3,
        description="最小Cry Episode継続時間（秒）",
        ge=0.1,
        le=5.0
    )

    energy_threshold: Optional[float] = Field(
        default=0.01,
        description="音声活動検出のエネルギー閾値",
        ge=0.001,
        le=0.1
    )


class AnalysisRequestSchema(BaseModel):
    """解析リクエストスキーマ"""
    file_id: int
    parameters: Optional[AnalysisParametersSchema] = None


class AnalysisStatusSchema(BaseModel):
    """解析ステータススキーマ"""
    file_id: int
    status: str  # 'uploaded', 'processing', 'completed', 'failed'
    message: str
    progress: Optional[int] = None  # 進捗率（0-100）
    task_id: Optional[str] = None  # CeleryタスクID
