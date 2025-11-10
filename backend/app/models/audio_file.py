from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # システム内部のファイル名（UUID）
    original_filename = Column(String(255), nullable=False)  # ユーザーがアップロードした元のファイル名
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # バイト単位
    sample_rate = Column(Integer, nullable=True)  # Hz
    duration = Column(Float, nullable=True)  # 秒
    recording_start_time = Column(DateTime(timezone=True), nullable=True, index=True)  # 録音開始時刻（オプション）
    status = Column(String(50), nullable=False, default="uploaded", index=True)  # 'uploaded', 'processing', 'completed', 'failed'
    task_id = Column(String(255), nullable=True)  # Celeryタスク ID
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション
    user = relationship("User", back_populates="audio_files")
    analysis_results = relationship("AnalysisResult", back_populates="audio_file", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="audio_file_tags", back_populates="audio_files")

    # チェック制約
    __table_args__ = (
        CheckConstraint(
            "status IN ('uploaded', 'processing', 'completed', 'failed')",
            name="check_status"
        ),
    )
