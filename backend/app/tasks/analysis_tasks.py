from celery import Task
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.audio_file import AudioFile
from app.models.analysis_result import AnalysisResult
from app.audio.cry_detector import CryDetector
from app.audio.cry_unit_detector import CryUnitDetector
from app.audio.acoustic_analyzer import AcousticAnalyzer
import librosa
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """データベースセッションを管理するタスク基底クラス"""
    _db: Session = None

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db


@celery_app.task(base=DatabaseTask, bind=True)
def analyze_audio_file(self, file_id: int):
    """
    音声ファイルを解析するタスク

    Args:
        file_id: 音声ファイルID

    Returns:
        解析結果ID
    """
    logger.info(f"Starting analysis for file_id={file_id}")

    try:
        # データベースからファイル情報を取得
        audio_file = self.db.query(AudioFile).filter(AudioFile.id == file_id).first()

        if not audio_file:
            raise ValueError(f"Audio file {file_id} not found")

        # ステータスを'processing'に更新
        audio_file.status = "processing"
        self.db.commit()

        # 進捗: 10% - ファイル読み込み完了
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': 'File loaded'})

        # 泣き声を検出
        logger.info(f"Detecting cry episodes for file_id={file_id}")
        cry_detector = CryDetector()

        # 進捗: 20% - 泣き声検出開始
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': 'Detecting cry episodes'})

        cry_episodes = cry_detector.detect_from_file(audio_file.file_path)

        # 進捗: 40% - 泣き声検出完了
        self.update_state(state='PROGRESS', meta={'progress': 40, 'message': f'Found {len(cry_episodes)} episodes'})

        # 泣き声エピソードを辞書形式に変換（numpy型をPython型に変換）
        cry_episodes_data = [
            {
                "start_time": float(ep.start_time),
                "end_time": float(ep.end_time),
                "duration": float(ep.duration),
                "confidence": float(ep.confidence)
            }
            for ep in cry_episodes
        ]

        # 音響解析
        logger.info(f"Analyzing acoustic features for file_id={file_id}")
        acoustic_analyzer = AcousticAnalyzer()

        # Cry Unit検出器を初期化
        cry_unit_detector = CryUnitDetector()

        # 進捗: 50% - 音響解析開始
        self.update_state(state='PROGRESS', meta={'progress': 50, 'message': 'Loading audio for analysis'})

        # 音声ファイル全体を読み込み（Cry Unit検出用）
        logger.info(f"Loading full audio for cry unit detection, file_id={file_id}")
        y_full, sr = librosa.load(audio_file.file_path, sr=22050)

        # 各エピソードの音響特徴を解析
        episodes_features = {}
        episodes_statistics = {}
        episodes_cry_units = {}

        total_episodes = len(cry_episodes)
        for i, episode in enumerate(cry_episodes):
            segment_id = f"episode_{i}"

            # 各エピソード処理の基準進捗（50-80%の範囲で）
            base_progress = 50 + int((i / max(total_episodes, 1)) * 30)
            step_size = int(30 / max(total_episodes, 1) / 15)  # 各エピソードを15ステップに分割（音響特徴抽出を10ステップに細分化）

            # 音響特徴抽出の進捗コールバック
            def acoustic_progress_callback(substep, message):
                progress = base_progress + int(substep * step_size)
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'message': f'Episode {i+1}/{total_episodes}: {message}'}
                )

            # ステップ1-10: 音響特徴解析（内部で細分化されたサブステップ）
            features = acoustic_analyzer.analyze_segment(
                audio_file.file_path,
                episode.start_time,
                episode.end_time,
                progress_callback=acoustic_progress_callback
            )

            # 辞書形式に変換
            features_data = [f.to_dict() for f in features]
            episodes_features[segment_id] = features_data

            # ステップ11: 統計量計算
            self.update_state(
                state='PROGRESS',
                meta={'progress': base_progress + step_size * 11, 'message': f'Episode {i+1}/{total_episodes}: Computing statistics'}
            )
            statistics = acoustic_analyzer.compute_statistics(features)

            # ステップ12: 特殊パラメータ計算
            self.update_state(
                state='PROGRESS',
                meta={'progress': base_progress + step_size * 12, 'message': f'Episode {i+1}/{total_episodes}: Computing special parameters'}
            )
            special_params = acoustic_analyzer.compute_special_parameters(features)

            # ステップ13: Cry Unit検出
            self.update_state(
                state='PROGRESS',
                meta={'progress': base_progress + step_size * 13, 'message': f'Episode {i+1}/{total_episodes}: Detecting cry units'}
            )
            logger.info(f"Detecting cry units for {segment_id}, file_id={file_id}")
            cry_units = cry_unit_detector.detect_units_in_episode(
                y_full,
                episode.start_time,
                episode.end_time
            )

            # ステップ14: Cry Unitメトリクス計算
            self.update_state(
                state='PROGRESS',
                meta={'progress': base_progress + step_size * 14, 'message': f'Episode {i+1}/{total_episodes}: Computing cry unit metrics'}
            )
            cryCE, unvoicedCE = cry_unit_detector.calculate_cry_unit_metrics(cry_units)

            # Cry Unitデータを辞書形式に変換（numpy型をPython型に変換）
            cry_units_data = [
                {
                    "start_time": float(unit.start_time),
                    "end_time": float(unit.end_time),
                    "duration": float(unit.duration),
                    "is_voiced": bool(unit.is_voiced),
                    "mean_energy": float(unit.mean_energy),
                    "peak_frequency": float(unit.peak_frequency)
                }
                for unit in cry_units
            ]

            episodes_cry_units[segment_id] = {
                "units": cry_units_data,
                "unit_count": len(cry_units),
                "cryCE": float(cryCE),
                "unvoicedCE": float(unvoicedCE)
            }

            # 統計量と特殊パラメータにCry Unit関連メトリクスを追加
            episodes_statistics[segment_id] = {
                **statistics,
                **special_params,
                "cryCE": float(cryCE),
                "unvoicedCE": float(unvoicedCE),
                "cry_unit_count": int(len(cry_units))
            }

        # 進捗: 85% - 解析完了、保存準備
        self.update_state(state='PROGRESS', meta={'progress': 85, 'message': 'Saving results'})

        # 解析結果をまとめる
        result_data = {
            "cry_episodes": cry_episodes_data,
            "acoustic_features": episodes_features,
            "statistics": episodes_statistics,
            "cry_units": episodes_cry_units
        }

        # 解析結果をデータベースに保存
        analysis_result = AnalysisResult(
            audio_file_id=file_id,
            result_data=result_data
        )
        self.db.add(analysis_result)

        # ファイルのステータスを'completed'に更新
        audio_file.status = "completed"
        self.db.commit()

        # 進捗: 100% - 完了
        self.update_state(state='PROGRESS', meta={'progress': 100, 'message': 'Analysis completed'})

        logger.info(f"Analysis completed for file_id={file_id}, result_id={analysis_result.id}")

        return analysis_result.id

    except Exception as e:
        logger.error(f"Analysis failed for file_id={file_id}: {str(e)}")

        # エラーが発生した場合、ステータスを'failed'に更新
        audio_file = self.db.query(AudioFile).filter(AudioFile.id == file_id).first()
        if audio_file:
            audio_file.status = "failed"
            self.db.commit()

        raise
