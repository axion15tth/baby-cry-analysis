from pydantic import BaseModel, Field
from typing import Optional


class AnalysisParameters(BaseModel):
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


class AnalysisRequest(BaseModel):
    """解析リクエスト"""

    file_id: int
    auto_analyze: bool = True
    parameters: Optional[AnalysisParameters] = None
