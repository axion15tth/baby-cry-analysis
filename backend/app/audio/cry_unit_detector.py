import numpy as np
import librosa
from typing import List, Tuple
from dataclasses import dataclass
import scipy.signal


@dataclass
class CryUnit:
    """Cry Unitのデータクラス"""
    start_time: float  # 開始時刻（秒）
    end_time: float    # 終了時刻（秒）
    duration: float    # 継続時間（秒）
    is_voiced: bool    # 有声音かどうか
    mean_energy: float # 平均エネルギー
    peak_frequency: float  # ピーク周波数（Hz）


class CryUnitDetector:
    """
    Cry Unit検出器

    Cry Episode内の呼気相ごとの分割を行い、
    各Cry Unitを検出します。
    """

    def __init__(
        self,
        sr: int = 22050,
        silence_threshold: float = 0.01,  # 無音判定閾値
        min_unit_duration: float = 0.1,   # 最小Cry Unit継続時間（秒）
        min_silence_duration: float = 0.05,  # 最小無音継続時間（秒）
        voiced_threshold: float = 0.3      # 有声音判定閾値（HNR）
    ):
        """
        Args:
            sr: サンプリングレート
            silence_threshold: 無音判定のエネルギー閾値
            min_unit_duration: 最小Cry Unit継続時間
            min_silence_duration: 最小無音継続時間（呼気と吸気の境界）
            voiced_threshold: 有声音判定閾値（Harmonics-to-Noise Ratio）
        """
        self.sr = sr
        self.silence_threshold = silence_threshold
        self.min_unit_duration = min_unit_duration
        self.min_silence_duration = min_silence_duration
        self.voiced_threshold = voiced_threshold

    def detect_units_in_episode(
        self,
        y: np.ndarray,
        episode_start_time: float,
        episode_end_time: float
    ) -> List[CryUnit]:
        """
        Cry Episode内のCry Unitを検出

        Args:
            y: 音声データ全体
            episode_start_time: エピソードの開始時刻（秒）
            episode_end_time: エピソードの終了時刻（秒）

        Returns:
            検出されたCry Unitのリスト
        """
        # エピソードの区間を抽出
        start_sample = int(episode_start_time * self.sr)
        end_sample = int(episode_end_time * self.sr)
        episode_audio = y[start_sample:end_sample]

        if len(episode_audio) == 0:
            return []

        # 音声パワーエンベロープを計算
        hop_length = 512
        frame_duration = hop_length / self.sr

        # RMS（Root Mean Square）エネルギーを計算
        energy = librosa.feature.rms(y=episode_audio, hop_length=hop_length)[0]

        # エンベロープをスムージング
        window_length = 5
        if len(energy) >= window_length:
            energy = scipy.signal.savgol_filter(energy, window_length, 2)

        # 無音区間を検出
        silence_frames = energy < self.silence_threshold

        # 連続する無音区間を検出
        silence_segments = self._find_silence_segments(
            silence_frames,
            frame_duration
        )

        # Cry Unitの境界を特定
        unit_boundaries = self._determine_unit_boundaries(
            silence_segments,
            len(energy) * frame_duration
        )

        # 各Cry Unitの特徴を計算
        units = []
        for i, (unit_start, unit_end) in enumerate(unit_boundaries):
            # 絶対時刻に変換
            abs_start = episode_start_time + unit_start
            abs_end = episode_start_time + unit_end

            # 最小継続時間をチェック
            if (abs_end - abs_start) < self.min_unit_duration:
                continue

            # この区間の音声データを抽出
            unit_start_sample = int(unit_start * self.sr)
            unit_end_sample = int(unit_end * self.sr)
            unit_audio = episode_audio[unit_start_sample:unit_end_sample]

            if len(unit_audio) == 0:
                continue

            # 有声音/無声音を判定
            is_voiced = self._classify_voicing(unit_audio)

            # 平均エネルギーを計算
            unit_energy_frames = energy[
                int(unit_start / frame_duration):int(unit_end / frame_duration)
            ]
            mean_energy = float(np.mean(unit_energy_frames)) if len(unit_energy_frames) > 0 else 0.0

            # ピーク周波数を計算
            peak_freq = self._estimate_peak_frequency(unit_audio)

            unit = CryUnit(
                start_time=abs_start,
                end_time=abs_end,
                duration=abs_end - abs_start,
                is_voiced=is_voiced,
                mean_energy=mean_energy,
                peak_frequency=peak_freq
            )
            units.append(unit)

        return units

    def _find_silence_segments(
        self,
        silence_frames: np.ndarray,
        frame_duration: float
    ) -> List[Tuple[float, float]]:
        """
        連続する無音区間を検出

        Args:
            silence_frames: 各フレームが無音かどうかのブール配列
            frame_duration: 1フレームの時間（秒）

        Returns:
            (開始時刻, 終了時刻)のリスト
        """
        segments = []
        in_silence = False
        silence_start = 0

        for i, is_silence in enumerate(silence_frames):
            if is_silence and not in_silence:
                # 無音区間開始
                in_silence = True
                silence_start = i
            elif not is_silence and in_silence:
                # 無音区間終了
                in_silence = False
                silence_duration = (i - silence_start) * frame_duration

                # 最小無音継続時間をチェック
                if silence_duration >= self.min_silence_duration:
                    start_time = silence_start * frame_duration
                    end_time = i * frame_duration
                    segments.append((start_time, end_time))

        # 最後の無音区間を処理
        if in_silence:
            silence_duration = (len(silence_frames) - silence_start) * frame_duration
            if silence_duration >= self.min_silence_duration:
                start_time = silence_start * frame_duration
                end_time = len(silence_frames) * frame_duration
                segments.append((start_time, end_time))

        return segments

    def _determine_unit_boundaries(
        self,
        silence_segments: List[Tuple[float, float]],
        total_duration: float
    ) -> List[Tuple[float, float]]:
        """
        無音区間に基づいてCry Unitの境界を特定

        Args:
            silence_segments: 無音区間のリスト
            total_duration: エピソードの総時間（秒）

        Returns:
            Cry Unitの(開始時刻, 終了時刻)のリスト
        """
        if not silence_segments:
            # 無音区間がない場合、全体を1つのUnitとする
            return [(0.0, total_duration)]

        boundaries = []
        current_start = 0.0

        for silence_start, silence_end in silence_segments:
            # 無音区間の前までを1つのUnitとする
            if silence_start > current_start:
                boundaries.append((current_start, silence_start))

            # 次のUnitは無音区間の後から
            current_start = silence_end

        # 最後のUnit
        if current_start < total_duration:
            boundaries.append((current_start, total_duration))

        return boundaries

    def _classify_voicing(self, audio: np.ndarray) -> bool:
        """
        音声が有声音かどうかを判定

        Args:
            audio: 音声データ

        Returns:
            有声音ならTrue、無声音ならFalse
        """
        if len(audio) < self.sr * 0.02:  # 20ms未満は判定できない
            return False

        # Zero Crossing Rateを計算
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        mean_zcr = np.mean(zcr)

        # 有声音はZCRが低い（周期的な波形）
        # 無声音はZCRが高い（ノイズ的な波形）
        # 閾値: 0.1（調整可能）
        is_voiced = mean_zcr < 0.1

        # エネルギーもチェック（無声音は一般的にエネルギーが低い）
        energy = np.sqrt(np.mean(audio ** 2))
        if energy < 0.01:
            is_voiced = False

        return is_voiced

    def _estimate_peak_frequency(self, audio: np.ndarray) -> float:
        """
        ピーク周波数を推定

        Args:
            audio: 音声データ

        Returns:
            ピーク周波数（Hz）
        """
        if len(audio) < 512:
            return 0.0

        # FFTを使用してスペクトルを計算
        fft = np.fft.rfft(audio)
        magnitude = np.abs(fft)

        # ピーク周波数を見つける
        peak_idx = np.argmax(magnitude)
        peak_freq = peak_idx * self.sr / (2 * len(magnitude))

        return float(peak_freq)

    def calculate_cry_unit_metrics(
        self,
        units: List[CryUnit]
    ) -> Tuple[float, float]:
        """
        Cry Unit関連のメトリクスを計算

        Args:
            units: Cry Unitのリスト

        Returns:
            (cryCE, unvoicedCE)のタプル
            - cryCE: 平均Cry Unit継続時間（有声音のみ）
            - unvoicedCE: 無声音Cry Unitの継続時間の合計
        """
        if not units:
            return 0.0, 0.0

        # 有声音Cry Unitの平均継続時間
        voiced_units = [u for u in units if u.is_voiced]
        if voiced_units:
            cryCE = np.mean([u.duration for u in voiced_units])
        else:
            cryCE = 0.0

        # 無声音Cry Unitの継続時間の合計
        unvoiced_units = [u for u in units if not u.is_voiced]
        if unvoiced_units:
            unvoicedCE = sum([u.duration for u in unvoiced_units])
        else:
            unvoicedCE = 0.0

        return float(cryCE), float(unvoicedCE)
