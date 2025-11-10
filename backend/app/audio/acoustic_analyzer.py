import numpy as np
import parselmouth
from parselmouth.praat import call
import librosa
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AcousticFeatures:
    """音響特徴のデータクラス"""
    time: float                    # 時刻（秒）
    f0: Optional[float]           # 基本周波数（Hz）
    f1: Optional[float]           # 第1フォルマント（Hz）
    f2: Optional[float]           # 第2フォルマント（Hz）
    f3: Optional[float]           # 第3フォルマント（Hz）
    hnr: Optional[float]          # Harmonics-to-Noise Ratio（dB）
    shimmer: Optional[float]      # Shimmer（振幅変動、%）
    jitter: Optional[float]       # Jitter（周期変動、%）
    intensity: Optional[float]    # 音圧（dB）

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return asdict(self)


class AcousticAnalyzer:
    """
    音響解析器

    Parselmouthを使用して音響パラメータを計算します。
    - F0（基本周波数）
    - フォルマント（F1, F2, F3）
    - HNR（Harmonics-to-Noise Ratio）
    - Shimmer（振幅変動）
    - Jitter（周期変動）
    - Intensity（音圧）
    """

    def __init__(
        self,
        time_step: float = 0.01,     # 10ms単位
        f0_min: float = 75.0,        # 最小F0（Hz）
        f0_max: float = 600.0,       # 最大F0（Hz）
        max_formants: int = 5        # フォルマント数
    ):
        """
        Args:
            time_step: 解析時間ステップ（秒）
            f0_min: 最小基本周波数
            f0_max: 最大基本周波数
            max_formants: フォルマント数
        """
        self.time_step = time_step
        self.f0_min = f0_min
        self.f0_max = f0_max
        self.max_formants = max_formants

    def analyze_segment(
        self,
        file_path: str,
        start_time: float,
        end_time: float,
        progress_callback=None
    ) -> List[AcousticFeatures]:
        """
        音声ファイルの指定区間を解析

        Args:
            file_path: 音声ファイルのパス
            start_time: 開始時刻（秒）
            end_time: 終了時刻（秒）
            progress_callback: 進捗コールバック関数 callback(step, message)

        Returns:
            時系列の音響特徴リスト
        """
        # Parselmouthで音声を読み込み
        if progress_callback:
            progress_callback(1, "Loading audio segment")
        sound = parselmouth.Sound(file_path)

        # 指定区間を抽出
        if progress_callback:
            progress_callback(2, "Extracting segment")
        segment = sound.extract_part(
            from_time=start_time,
            to_time=end_time,
            preserve_times=True
        )

        # 各パラメータを計算
        features_list = []

        # F0を計算
        if progress_callback:
            progress_callback(3, "Computing F0 (pitch)")
        pitch = segment.to_pitch(time_step=self.time_step, pitch_floor=self.f0_min, pitch_ceiling=self.f0_max)

        # フォルマントを計算
        if progress_callback:
            progress_callback(4, "Computing formants")
        formants = segment.to_formant_burg(time_step=self.time_step, max_number_of_formants=self.max_formants)

        # PointProcessを作成（JitterとShimmer計算に必要）
        if progress_callback:
            progress_callback(5, "Creating point process")
        point_process = call(segment, "To PointProcess (periodic, cc)", self.f0_min, self.f0_max)

        # Intensityを計算
        if progress_callback:
            progress_callback(6, "Computing intensity")
        intensity = segment.to_intensity(time_step=self.time_step)

        # HNRを計算（ループの外で一度だけ）
        if progress_callback:
            progress_callback(6.5, "Computing harmonicity (HNR)")
        try:
            harmonicity = segment.to_harmonicity(time_step=self.time_step)
        except:
            harmonicity = None

        # Jitter/Shimmerを計算（ループの外で一度だけ - セグメント全体の統計値）
        if progress_callback:
            progress_callback(6.7, "Computing jitter and shimmer")
        try:
            jitter_value = call(point_process, "Get jitter (local)", start_time, end_time, 0.0001, 0.02, 1.3)
            jitter = jitter_value * 100 if jitter_value and not np.isnan(jitter_value) else None
        except:
            jitter = None

        try:
            shimmer_value = call([segment, point_process], "Get shimmer (local)", start_time, end_time, 0.0001, 0.02, 1.3, 1.6)
            shimmer = shimmer_value * 100 if shimmer_value and not np.isnan(shimmer_value) else None
        except:
            shimmer = None

        # 時系列で解析
        times = pitch.xs()
        total_frames = len(times)

        for idx, t in enumerate(times):
            # 10%ごとに進捗を報告
            if progress_callback and idx % max(1, total_frames // 10) == 0:
                progress_pct = int((idx / total_frames) * 100)
                progress_callback(7 + (idx / total_frames) * 3, f"Extracting features: frame {idx+1}/{total_frames} ({progress_pct}%)")

            # F0
            f0_value = pitch.get_value_at_time(t)
            f0 = f0_value if f0_value and not np.isnan(f0_value) else None

            # フォルマント
            f1 = formants.get_value_at_time(1, t) if t <= formants.xmax else None
            f2 = formants.get_value_at_time(2, t) if t <= formants.xmax else None
            f3 = formants.get_value_at_time(3, t) if t <= formants.xmax else None

            # NaN チェック
            f1 = f1 if f1 and not np.isnan(f1) else None
            f2 = f2 if f2 and not np.isnan(f2) else None
            f3 = f3 if f3 and not np.isnan(f3) else None

            # HNR（事前計算済み）
            if harmonicity:
                try:
                    hnr_value = harmonicity.get_value(time=t)
                    hnr = hnr_value if hnr_value and not np.isnan(hnr_value) else None
                except:
                    hnr = None
            else:
                hnr = None

            # Intensity
            intensity_value = intensity.get_value(time=t)
            intensity_db = intensity_value if intensity_value and not np.isnan(intensity_value) else None

            features = AcousticFeatures(
                time=t,
                f0=f0,
                f1=f1,
                f2=f2,
                f3=f3,
                hnr=hnr,
                shimmer=shimmer,
                jitter=jitter,
                intensity=intensity_db
            )

            features_list.append(features)

        return features_list

    def analyze_file(
        self,
        file_path: str,
        segments: Optional[List[tuple]] = None
    ) -> Dict[str, List[AcousticFeatures]]:
        """
        音声ファイル全体または指定されたセグメントを解析

        Args:
            file_path: 音声ファイルのパス
            segments: [(start_time, end_time), ...] のリスト。Noneの場合はファイル全体

        Returns:
            セグメントごとの音響特徴の辞書
        """
        if segments is None:
            # ファイル全体を解析
            sound = parselmouth.Sound(file_path)
            duration = sound.duration
            segments = [(0.0, duration)]

        results = {}

        for i, (start, end) in enumerate(segments):
            segment_id = f"segment_{i}"
            features = self.analyze_segment(file_path, start, end)
            results[segment_id] = features

        return results

    def compute_statistics(
        self,
        features_list: List[AcousticFeatures]
    ) -> Dict[str, Dict[str, float]]:
        """
        音響特徴の統計量を計算

        Args:
            features_list: 音響特徴のリスト

        Returns:
            各パラメータの統計量（平均、標準偏差、最小値、最大値）
        """
        # パラメータごとに値を抽出
        params = ['f0', 'f1', 'f2', 'f3', 'hnr', 'shimmer', 'jitter', 'intensity']
        statistics = {}

        for param in params:
            values = [getattr(f, param) for f in features_list if getattr(f, param) is not None]

            if values:
                statistics[param] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'median': float(np.median(values))
                }
            else:
                statistics[param] = {
                    'mean': None,
                    'std': None,
                    'min': None,
                    'max': None,
                    'median': None
                }

        return statistics

    def compute_special_parameters(
        self,
        features_list: List[AcousticFeatures],
        high_pitch_threshold: float = 500.0
    ) -> Dict[str, float]:
        """
        特殊パラメータを計算

        Args:
            features_list: 音響特徴のリスト
            high_pitch_threshold: High-pitchの閾値（Hz）

        Returns:
            特殊パラメータの辞書
            - high_pitch_pct: High-pitch割合（%）
            - hyper_phonation_pct: Hyper-phonation割合（%）
            - voiced_pct: 有声音割合（%）
            - unvoiced_pct: 無声音割合（%）
        """
        total_frames = len(features_list)

        if total_frames == 0:
            return {
                'high_pitch_pct': 0.0,
                'hyper_phonation_pct': 0.0,
                'voiced_pct': 0.0,
                'unvoiced_pct': 0.0
            }

        # High-pitch割合
        high_pitch_count = sum(
            1 for f in features_list
            if f.f0 is not None and f.f0 > high_pitch_threshold
        )
        high_pitch_pct = (high_pitch_count / total_frames) * 100

        # Hyper-phonation割合
        # 定義: HNR < 10dB AND Shimmer > 5% AND Jitter > 1%
        hyper_phonation_count = sum(
            1 for f in features_list
            if (f.hnr is not None and f.hnr < 10.0 and
                f.shimmer is not None and f.shimmer > 5.0 and
                f.jitter is not None and f.jitter > 1.0)
        )
        hyper_phonation_pct = (hyper_phonation_count / total_frames) * 100

        # 有声音/無声音の割合
        # F0が検出された（Noneでない）フレームを有声音とみなす
        voiced_count = sum(1 for f in features_list if f.f0 is not None)
        unvoiced_count = total_frames - voiced_count

        voiced_pct = (voiced_count / total_frames) * 100
        unvoiced_pct = (unvoiced_count / total_frames) * 100

        return {
            'high_pitch_pct': round(high_pitch_pct, 2),
            'hyper_phonation_pct': round(hyper_phonation_pct, 2),
            'voiced_pct': round(voiced_pct, 2),
            'unvoiced_pct': round(unvoiced_pct, 2)
        }
