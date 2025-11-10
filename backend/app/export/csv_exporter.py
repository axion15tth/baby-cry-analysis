import csv
from io import StringIO
from typing import Dict, Any, Optional
from datetime import datetime

from app.utils.time_utils import seconds_to_absolute_time, format_datetime, format_seconds


class CSVExporter:
    """CSV形式で解析結果をエクスポート"""

    def export_cry_episodes(
        self,
        result_data: Dict[str, Any],
        recording_start_time: Optional[datetime] = None
    ) -> str:
        """
        泣き声エピソードをCSV形式でエクスポート

        Args:
            result_data: 解析結果データ
            recording_start_time: 録音開始時刻

        Returns:
            CSV文字列
        """
        output = StringIO()
        writer = csv.writer(output)

        # ヘッダー
        if recording_start_time:
            writer.writerow([
                "エピソード番号",
                "開始時刻（絶対）",
                "終了時刻（絶対）",
                "開始時刻（相対秒）",
                "終了時刻（相対秒）",
                "継続時間（秒）",
                "信頼度"
            ])
        else:
            writer.writerow([
                "エピソード番号",
                "開始時刻（秒）",
                "終了時刻（秒）",
                "継続時間（秒）",
                "信頼度"
            ])

        # データ行
        cry_episodes = result_data.get("cry_episodes", [])
        for i, episode in enumerate(cry_episodes, 1):
            start_time = episode["start_time"]
            end_time = episode["end_time"]
            duration = episode["duration"]
            confidence = episode["confidence"]

            if recording_start_time:
                abs_start = seconds_to_absolute_time(recording_start_time, start_time)
                abs_end = seconds_to_absolute_time(recording_start_time, end_time)
                writer.writerow([
                    i,
                    format_datetime(abs_start),
                    format_datetime(abs_end),
                    format_seconds(start_time),
                    format_seconds(end_time),
                    format_seconds(duration),
                    f"{confidence:.4f}"
                ])
            else:
                writer.writerow([
                    i,
                    format_seconds(start_time),
                    format_seconds(end_time),
                    format_seconds(duration),
                    f"{confidence:.4f}"
                ])

        return output.getvalue()

    def export_acoustic_features(
        self,
        result_data: Dict[str, Any],
        episode_id: str,
        recording_start_time: Optional[datetime] = None
    ) -> str:
        """
        音響特徴をCSV形式でエクスポート

        Args:
            result_data: 解析結果データ
            episode_id: エピソードID（例: "episode_0"）
            recording_start_time: 録音開始時刻

        Returns:
            CSV文字列
        """
        output = StringIO()
        writer = csv.writer(output)

        # ヘッダー
        if recording_start_time:
            writer.writerow([
                "時刻（絶対）",
                "時刻（相対秒）",
                "F0 (Hz)",
                "F1 (Hz)",
                "F2 (Hz)",
                "F3 (Hz)",
                "HNR (dB)",
                "Shimmer (%)",
                "Jitter (%)",
                "Intensity (dB)"
            ])
        else:
            writer.writerow([
                "時刻（秒）",
                "F0 (Hz)",
                "F1 (Hz)",
                "F2 (Hz)",
                "F3 (Hz)",
                "HNR (dB)",
                "Shimmer (%)",
                "Jitter (%)",
                "Intensity (dB)"
            ])

        # データ行
        acoustic_features = result_data.get("acoustic_features", {})
        features_list = acoustic_features.get(episode_id, [])

        for feature in features_list:
            time = feature["time"]

            def format_value(v):
                if v is None:
                    return ""
                return f"{v:.4f}"

            if recording_start_time:
                abs_time = seconds_to_absolute_time(recording_start_time, time)
                writer.writerow([
                    format_datetime(abs_time),
                    format_seconds(time),
                    format_value(feature.get("f0")),
                    format_value(feature.get("f1")),
                    format_value(feature.get("f2")),
                    format_value(feature.get("f3")),
                    format_value(feature.get("hnr")),
                    format_value(feature.get("shimmer")),
                    format_value(feature.get("jitter")),
                    format_value(feature.get("intensity"))
                ])
            else:
                writer.writerow([
                    format_seconds(time),
                    format_value(feature.get("f0")),
                    format_value(feature.get("f1")),
                    format_value(feature.get("f2")),
                    format_value(feature.get("f3")),
                    format_value(feature.get("hnr")),
                    format_value(feature.get("shimmer")),
                    format_value(feature.get("jitter")),
                    format_value(feature.get("intensity"))
                ])

        return output.getvalue()

    def export_statistics(
        self,
        result_data: Dict[str, Any],
        episode_id: str
    ) -> str:
        """
        統計情報をCSV形式でエクスポート

        Args:
            result_data: 解析結果データ
            episode_id: エピソードID（例: "episode_0"）

        Returns:
            CSV文字列
        """
        output = StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow(["パラメータ", "平均", "標準偏差", "最小値", "最大値", "中央値"])

        # データ行
        statistics = result_data.get("statistics", {})
        episode_stats = statistics.get(episode_id, {})

        def format_value(v):
            if v is None:
                return ""
            return f"{v:.4f}"

        # 音響パラメータの統計量（標準的な統計値を持つもの）
        acoustic_params = ['f0', 'f1', 'f2', 'f3', 'hnr', 'shimmer', 'jitter', 'intensity']

        for param in acoustic_params:
            if param in episode_stats:
                stats = episode_stats[param]
                writer.writerow([
                    param.upper(),
                    format_value(stats.get("mean")),
                    format_value(stats.get("std")),
                    format_value(stats.get("min")),
                    format_value(stats.get("max")),
                    format_value(stats.get("median"))
                ])

        # 特殊パラメータ（パーセンテージ値）
        writer.writerow([])  # 空行
        writer.writerow(["特殊パラメータ", "値 (%)", "", "", "", ""])

        special_params = [
            ('high_pitch_pct', 'High-pitch割合'),
            ('hyper_phonation_pct', 'Hyper-phonation割合'),
            ('voiced_pct', '有声音割合'),
            ('unvoiced_pct', '無声音割合')
        ]

        for param_key, param_label in special_params:
            if param_key in episode_stats:
                value = episode_stats[param_key]
                writer.writerow([
                    param_label,
                    format_value(value),
                    "",
                    "",
                    "",
                    ""
                ])

        return output.getvalue()

    def export_cry_units(
        self,
        result_data: Dict[str, Any],
        episode_id: str,
        recording_start_time: Optional[datetime] = None
    ) -> str:
        """
        Cry UnitをCSV形式でエクスポート

        Args:
            result_data: 解析結果データ
            episode_id: エピソードID（例: "episode_0"）
            recording_start_time: 録音開始時刻

        Returns:
            CSV文字列
        """
        output = StringIO()
        writer = csv.writer(output)

        # ヘッダー
        if recording_start_time:
            writer.writerow([
                "Cry Unit番号",
                "開始時刻（絶対）",
                "終了時刻（絶対）",
                "開始時刻（相対秒）",
                "終了時刻（相対秒）",
                "継続時間（秒）",
                "有声音/無声音",
                "平均エネルギー",
                "ピーク周波数 (Hz)"
            ])
        else:
            writer.writerow([
                "Cry Unit番号",
                "開始時刻（秒）",
                "終了時刻（秒）",
                "継続時間（秒）",
                "有声音/無声音",
                "平均エネルギー",
                "ピーク周波数 (Hz)"
            ])

        # データ行
        cry_units_data = result_data.get("cry_units", {}).get(episode_id, {})
        units = cry_units_data.get("units", [])

        for i, unit in enumerate(units, 1):
            start_time = unit["start_time"]
            end_time = unit["end_time"]
            duration = unit["duration"]
            is_voiced = unit["is_voiced"]
            mean_energy = unit["mean_energy"]
            peak_frequency = unit["peak_frequency"]

            voicing_label = "有声音" if is_voiced else "無声音"

            if recording_start_time:
                abs_start = seconds_to_absolute_time(recording_start_time, start_time)
                abs_end = seconds_to_absolute_time(recording_start_time, end_time)
                writer.writerow([
                    i,
                    format_datetime(abs_start),
                    format_datetime(abs_end),
                    format_seconds(start_time),
                    format_seconds(end_time),
                    format_seconds(duration),
                    voicing_label,
                    f"{mean_energy:.6f}",
                    f"{peak_frequency:.2f}"
                ])
            else:
                writer.writerow([
                    i,
                    format_seconds(start_time),
                    format_seconds(end_time),
                    format_seconds(duration),
                    voicing_label,
                    f"{mean_energy:.6f}",
                    f"{peak_frequency:.2f}"
                ])

        return output.getvalue()
