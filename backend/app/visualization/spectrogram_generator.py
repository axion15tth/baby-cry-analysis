import numpy as np
import librosa
from typing import Dict, List, Any


class SpectrogramGenerator:
    """スペクトログラムデータ生成クラス"""

    def __init__(
        self,
        n_fft: int = 2048,
        hop_length: int = 512,
        max_freq: float = 8000.0,
        max_time_bins: int = 500
    ):
        """
        Args:
            n_fft: FFTウィンドウサイズ
            hop_length: ホップ長
            max_freq: 最大周波数（Hz）
            max_time_bins: 最大時間ビン数（ダウンサンプリング用）
        """
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.max_freq = max_freq
        self.max_time_bins = max_time_bins

    def generate_full_spectrogram(self, file_path: str) -> Dict[str, Any]:
        """
        ファイル全体のスペクトログラムデータを生成

        Args:
            file_path: 音声ファイルのパス

        Returns:
            スペクトログラムデータ（times, frequencies, spectrogram）
        """
        # 音声を読み込み
        y, sr = librosa.load(file_path, sr=None)

        # STFTを計算
        D = librosa.stft(y, n_fft=self.n_fft, hop_length=self.hop_length)

        # パワースペクトログラムに変換（dB）
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

        # 時間軸と周波数軸を生成
        times = librosa.frames_to_time(
            np.arange(S_db.shape[1]),
            sr=sr,
            hop_length=self.hop_length
        )
        frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)

        # 最大周波数でフィルタリング
        freq_mask = frequencies <= self.max_freq
        frequencies = frequencies[freq_mask]
        S_db = S_db[freq_mask, :]

        # 時間軸のダウンサンプリング
        if S_db.shape[1] > self.max_time_bins:
            indices = np.linspace(0, S_db.shape[1] - 1, self.max_time_bins, dtype=int)
            times = times[indices]
            S_db = S_db[:, indices]

        return {
            "times": times.tolist(),
            "frequencies": frequencies.tolist(),
            "spectrogram": S_db.tolist(),  # 2D array: [freq, time]
            "sample_rate": int(sr),
            "duration": float(len(y) / sr)
        }

    def generate_episode_spectrogram(
        self,
        file_path: str,
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """
        特定エピソードのスペクトログラムデータを生成

        Args:
            file_path: 音声ファイルのパス
            start_time: 開始時刻（秒）
            end_time: 終了時刻（秒）

        Returns:
            スペクトログラムデータ（times, frequencies, spectrogram）
        """
        # 音声を読み込み
        y, sr = librosa.load(file_path, sr=None)

        # エピソードの区間を抽出
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        y_segment = y[start_sample:end_sample]

        # STFTを計算
        D = librosa.stft(y_segment, n_fft=self.n_fft, hop_length=self.hop_length)

        # パワースペクトログラムに変換（dB）
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

        # 時間軸と周波数軸を生成（エピソード開始からの相対時刻）
        times = librosa.frames_to_time(
            np.arange(S_db.shape[1]),
            sr=sr,
            hop_length=self.hop_length
        )
        frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)

        # 最大周波数でフィルタリング
        freq_mask = frequencies <= self.max_freq
        frequencies = frequencies[freq_mask]
        S_db = S_db[freq_mask, :]

        # 時間軸のダウンサンプリング
        if S_db.shape[1] > self.max_time_bins:
            indices = np.linspace(0, S_db.shape[1] - 1, self.max_time_bins, dtype=int)
            times = times[indices]
            S_db = S_db[:, indices]

        return {
            "times": times.tolist(),
            "frequencies": frequencies.tolist(),
            "spectrogram": S_db.tolist(),  # 2D array: [freq, time]
            "sample_rate": int(sr),
            "duration": float(end_time - start_time),
            "start_time": float(start_time),
            "end_time": float(end_time)
        }
