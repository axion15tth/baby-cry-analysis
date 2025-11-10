from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False, index=True)
    result_data = Column(JSON, nullable=False)  # 解析結果データ（JSON）
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション
    audio_file = relationship("AudioFile", back_populates="analysis_results")
