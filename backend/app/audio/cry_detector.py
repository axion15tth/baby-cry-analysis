import numpy as np
import librosa
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class CryEpisode:
    """泣き声エピソードのデータクラス"""
    start_time: float  # 開始時刻（秒）
    end_time: float    # 終了時刻（秒）
    duration: float    # 継続時間（秒）
    confidence: float  # 信頼度（0-1）


class CryDetector:
    """
    泣き声検出器

    長時間（最大12時間）の音声データから泣き声エピソードを検出します。
    メモリ効率のためチャンク処理を使用します。
    """

    def __init__(
        self,
        sr: int = 22050,
        chunk_duration: int = 60,  # 1チャンク60秒
        energy_threshold: float = 0.02,
        min_duration: float = 0.5,  # 最小継続時間（秒）
        max_gap: float = 1.0,       # 最大ギャップ（秒）
        freq_min: int = 200,        # 泣き声の最小周波数（Hz）※スペクトルセントロイドを考慮して広めに設定
        freq_max: int = 5000        # 泣き声の最大周波数（Hz）※スペクトルセントロイドを考慮して広めに設定
    ):
        """
        Args:
            sr: サンプリングレート
            chunk_duration: 1チャンクの長さ（秒）
            energy_threshold: エネルギー閾値
            min_duration: 最小継続時間（秒）
            max_gap: エピソード間の最大ギャップ（秒）
            freq_min: 泣き声の最小周波数
            freq_max: 泣き声の最大周波数
        """
        self.sr = sr
        self.chunk_duration = chunk_duration
        self.energy_threshold = energy_threshold
        self.min_duration = min_duration
        self.max_gap = max_gap
        self.freq_min = freq_min
        self.freq_max = freq_max

    def detect_from_file(self, file_path: str) -> List[CryEpisode]:
        """
        音声ファイルから泣き声エピソードを検出

        Args:
            file_path: 音声ファイルのパス

        Returns:
            検出された泣き声エピソードのリスト
        """
        # ファイルの総時間を取得
        duration = librosa.get_duration(path=file_path)

        # チャンクごとに処理
        all_segments = []
        chunk_samples = int(self.chunk_duration * self.sr)

        for offset in np.arange(0, duration, self.chunk_duration):
            # チャンクを読み込み
            y, _ = librosa.load(
                file_path,
                sr=self.sr,
                offset=offset,
                duration=self.chunk_duration
            )

            # チャンク内の泣き声セグメントを検出
            segments = self._detect_cry_segments(y, offset)
            all_segments.extend(segments)

        # セグメントをエピソードにマージ
        episodes = self._merge_segments_to_episodes(all_segments)

        return episodes

    def _detect_cry_segments(
        self,
        y: np.ndarray,
        time_offset: float = 0.0
    ) -> List[Tuple[float, float, float]]:
        """
        音声チャンク内の泣き声セグメントを検出

        Args:
            y: 音声データ
            time_offset: このチャンクの開始時刻

        Returns:
            (開始時刻, 終了時刻, 信頼度)のリスト
        """
        segments = []

        # フレーム単位で処理
        hop_length = 512
        frame_duration = hop_length / self.sr

        # エネルギーを計算
        energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]

        # 周波数特徴を計算（スペクトルセントロイド）
        spectral_centroid = librosa.feature.spectral_centroid(
            y=y,
            sr=self.sr,
            hop_length=hop_length
        )[0]

        # 泣き声らしさを判定
        is_cry = self._is_cry_frame(energy, spectral_centroid)

        # 連続する泣き声フレームを検出
        in_segment = False
        segment_start = 0
        segment_energy_sum = 0
        segment_frames = 0

        for i, cry in enumerate(is_cry):
            if cry and not in_segment:
                # セグメント開始
                in_segment = True
                segment_start = i
                segment_energy_sum = energy[i]
                segment_frames = 1
            elif cry and in_segment:
                # セグメント継続
                segment_energy_sum += energy[i]
                segment_frames += 1
            elif not cry and in_segment:
                # セグメント終了
                in_segment = False
                segment_duration = segment_frames * frame_duration

                # 最小継続時間をチェック
                if segment_duration >= self.min_duration:
                    start_time = time_offset + segment_start * frame_duration
                    end_time = time_offset + i * frame_duration
                    confidence = min(segment_energy_sum / segment_frames / self.energy_threshold, 1.0)
                    segments.append((start_time, end_time, confidence))

        # 最後のセグメントを処理
        if in_segment:
            segment_duration = segment_frames * frame_duration
            if segment_duration >= self.min_duration:
                start_time = time_offset + segment_start * frame_duration
                end_time = time_offset + len(is_cry) * frame_duration
                confidence = min(segment_energy_sum / segment_frames / self.energy_threshold, 1.0)
                segments.append((start_time, end_time, confidence))

        return segments

    def _is_cry_frame(
        self,
        energy: np.ndarray,
        spectral_centroid: np.ndarray
    ) -> np.ndarray:
        """
        各フレームが泣き声かどうかを判定

        Args:
            energy: エネルギー
            spectral_centroid: スペクトル重心

        Returns:
            各フレームが泣き声かどうかのブール配列
        """
        # エネルギー条件
        energy_condition = energy > self.energy_threshold

        # 周波数条件（赤ちゃんの泣き声は300-600Hz程度）
        freq_condition = (spectral_centroid >= self.freq_min) & (spectral_centroid <= self.freq_max)

        return energy_condition & freq_condition

    def _merge_segments_to_episodes(
        self,
        segments: List[Tuple[float, float, float]]
    ) -> List[CryEpisode]:
        """
        セグメントをエピソードにマージ

        近接するセグメントを1つのエピソードにまとめます。

        Args:
            segments: (開始時刻, 終了時刻, 信頼度)のリスト

        Returns:
            CryEpisodeのリスト
        """
        if not segments:
            return []

        # 開始時刻でソート
        segments = sorted(segments, key=lambda x: x[0])

        episodes = []
        current_start = segments[0][0]
        current_end = segments[0][1]
        confidences = [segments[0][2]]

        for i in range(1, len(segments)):
            start, end, confidence = segments[i]

            # ギャップをチェック
            gap = start - current_end

            if gap <= self.max_gap:
                # エピソード継続
                current_end = end
                confidences.append(confidence)
            else:
                # エピソード終了、新規エピソード開始
                episode = CryEpisode(
                    start_time=current_start,
                    end_time=current_end,
                    duration=current_end - current_start,
                    confidence=np.mean(confidences)
                )
                episodes.append(episode)

                current_start = start
                current_end = end
                confidences = [confidence]

        # 最後のエピソードを追加
        episode = CryEpisode(
            start_time=current_start,
            end_time=current_end,
            duration=current_end - current_start,
            confidence=np.mean(confidences)
        )
        episodes.append(episode)

        return episodes
