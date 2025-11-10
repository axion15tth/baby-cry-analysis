import numpy as np
import librosa
from typing import Dict, List, Any


class WaveformGenerator:
    """波形データ生成クラス"""

    def __init__(self, max_points: int = 5000):
        """
        Args:
            max_points: 最大データポイント数（ダウンサンプリング用）
        """
        self.max_points = max_points

    def generate_full_waveform(self, file_path: str) -> Dict[str, Any]:
        """
        ファイル全体の波形データを生成

        Args:
            file_path: 音声ファイルのパス

        Returns:
            波形データ（time, amplitude, sample_rate）
        """
        # 音声を読み込み
        y, sr = librosa.load(file_path, sr=None)

        # 時間軸を生成
        times = np.arange(len(y)) / sr

        # データポイントが多すぎる場合はダウンサンプリング
        if len(y) > self.max_points:
            indices = np.linspace(0, len(y) - 1, self.max_points, dtype=int)
            times = times[indices]
            y = y[indices]

        return {
            "time": times.tolist(),
            "amplitude": y.tolist(),
            "sample_rate": int(sr),
            "duration": float(len(times) / sr) if len(times) > 0 else 0.0
        }

    def generate_episode_waveform(
        self,
        file_path: str,
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """
        特定エピソードの波形データを生成

        Args:
            file_path: 音声ファイルのパス
            start_time: 開始時刻（秒）
            end_time: 終了時刻（秒）

        Returns:
            波形データ（time, amplitude, sample_rate）
        """
        # 音声を読み込み
        y, sr = librosa.load(file_path, sr=None)

        # エピソードの区間を抽出
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)

        y_segment = y[start_sample:end_sample]

        # 時間軸を生成（エピソード開始からの相対時刻）
        times = np.arange(len(y_segment)) / sr

        # データポイントが多すぎる場合はダウンサンプリング
        if len(y_segment) > self.max_points:
            indices = np.linspace(0, len(y_segment) - 1, self.max_points, dtype=int)
            times = times[indices]
            y_segment = y_segment[indices]

        return {
            "time": times.tolist(),
            "amplitude": y_segment.tolist(),
            "sample_rate": int(sr),
            "duration": float(end_time - start_time),
            "start_time": float(start_time),
            "end_time": float(end_time)
        }
