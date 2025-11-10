from io import BytesIO
from typing import Dict, Any, Optional
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.utils.time_utils import seconds_to_absolute_time, format_datetime, format_seconds


class PDFExporter:
    """PDF形式で解析結果をエクスポート"""

    def __init__(self):
        # 日本語フォントの登録（デフォルトフォントを使用）
        self.styles = getSampleStyleSheet()

        # カスタムスタイル
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            alignment=TA_CENTER
        )

        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=10
        )

    def export(
        self,
        result_data: Dict[str, Any],
        file_info: Dict[str, Any],
        recording_start_time: Optional[datetime] = None
    ) -> bytes:
        """
        解析結果をPDF形式でエクスポート

        Args:
            result_data: 解析結果データ
            file_info: ファイル情報
            recording_start_time: 録音開始時刻

        Returns:
            PDFファイルのバイナリデータ
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # ドキュメント要素
        story = []

        # タイトル
        story.append(Paragraph("Baby Cry Analysis Report", self.title_style))
        story.append(Spacer(1, 12))

        # ファイル情報セクション
        story.extend(self._create_file_info_section(file_info, recording_start_time))
        story.append(Spacer(1, 12))

        # 解析サマリーセクション
        story.extend(self._create_summary_section(result_data))
        story.append(Spacer(1, 12))

        # 泣き声エピソードセクション
        story.extend(self._create_episodes_section(result_data, recording_start_time))
        story.append(PageBreak())

        # 音響特徴統計セクション
        story.extend(self._create_statistics_section(result_data))

        # PDFを生成
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _create_file_info_section(
        self,
        file_info: Dict[str, Any],
        recording_start_time: Optional[datetime]
    ):
        """ファイル情報セクション"""
        elements = []
        elements.append(Paragraph("File Information", self.heading_style))

        data = [
            ["Filename:", file_info.get("original_filename", "")],
            ["File Size:", f"{file_info.get('file_size', 0) / 1024:.2f} KB"],
            ["Recording Start:", format_datetime(recording_start_time) if recording_start_time else "Not set"],
            ["Analysis Date:", file_info.get("analyzed_at", "")],
        ]

        table = Table(data, colWidths=[50*mm, 100*mm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(table)
        return elements

    def _create_summary_section(self, result_data: Dict[str, Any]):
        """解析サマリーセクション"""
        elements = []
        elements.append(Paragraph("Analysis Summary", self.heading_style))

        cry_episodes = result_data.get("cry_episodes", [])
        total_cry_duration = sum(ep["duration"] for ep in cry_episodes)
        avg_duration = total_cry_duration / len(cry_episodes) if cry_episodes else 0

        data = [
            ["Detected Episodes:", str(len(cry_episodes))],
            ["Total Cry Duration:", f"{total_cry_duration:.2f} seconds"],
            ["Average Episode Length:", f"{avg_duration:.2f} seconds"],
        ]

        table = Table(data, colWidths=[50*mm, 100*mm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(table)
        return elements

    def _create_episodes_section(
        self,
        result_data: Dict[str, Any],
        recording_start_time: Optional[datetime]
    ):
        """泣き声エピソードセクション"""
        elements = []
        elements.append(Paragraph("Cry Episodes", self.heading_style))

        cry_episodes = result_data.get("cry_episodes", [])

        if recording_start_time:
            headers = [["No.", "Start (Abs)", "End (Abs)", "Duration", "Confidence"]]
        else:
            headers = [["No.", "Start (s)", "End (s)", "Duration (s)", "Confidence"]]

        data = headers.copy()

        for i, episode in enumerate(cry_episodes, 1):
            start_time = episode["start_time"]
            end_time = episode["end_time"]
            duration = episode["duration"]
            confidence = episode["confidence"]

            if recording_start_time:
                abs_start = seconds_to_absolute_time(recording_start_time, start_time)
                abs_end = seconds_to_absolute_time(recording_start_time, end_time)
                data.append([
                    str(i),
                    format_datetime(abs_start, "%H:%M:%S.%f"),
                    format_datetime(abs_end, "%H:%M:%S.%f"),
                    format_seconds(duration),
                    f"{confidence:.3f}"
                ])
            else:
                data.append([
                    str(i),
                    format_seconds(start_time),
                    format_seconds(end_time),
                    format_seconds(duration),
                    f"{confidence:.3f}"
                ])

        table = Table(data, colWidths=[15*mm, 35*mm, 35*mm, 25*mm, 25*mm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
        ]))

        elements.append(table)
        return elements

    def _create_statistics_section(self, result_data: Dict[str, Any]):
        """音響特徴統計セクション"""
        elements = []
        elements.append(Paragraph("Acoustic Features Statistics", self.heading_style))

        statistics = result_data.get("statistics", {})

        for episode_id, episode_stats in sorted(statistics.items()):
            episode_num = int(episode_id.split("_")[1]) + 1
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"Episode {episode_num}", self.styles['Heading3']))

            # 音響パラメータの統計量テーブル
            headers = [["Parameter", "Mean", "Std Dev", "Min", "Max", "Median"]]
            data = headers.copy()

            acoustic_params = ['f0', 'f1', 'f2', 'f3', 'hnr', 'shimmer', 'jitter', 'intensity']
            param_labels = {
                'f0': 'F0 (Hz)',
                'f1': 'F1 (Hz)',
                'f2': 'F2 (Hz)',
                'f3': 'F3 (Hz)',
                'hnr': 'HNR (dB)',
                'shimmer': 'Shimmer (%)',
                'jitter': 'Jitter (%)',
                'intensity': 'Intensity (dB)'
            }

            def fmt(v):
                return f"{v:.2f}" if v is not None else "N/A"

            for param in acoustic_params:
                if param in episode_stats:
                    stats = episode_stats[param]
                    data.append([
                        param_labels.get(param, param.upper()),
                        fmt(stats.get("mean")),
                        fmt(stats.get("std")),
                        fmt(stats.get("min")),
                        fmt(stats.get("max")),
                        fmt(stats.get("median"))
                    ])

            table = Table(data, colWidths=[30*mm, 25*mm, 25*mm, 25*mm, 25*mm, 25*mm])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 8))

            # 特殊パラメータテーブル
            elements.append(Paragraph("Special Parameters (%)", self.styles['Heading4']))
            special_headers = [["Parameter", "Value"]]
            special_data = special_headers.copy()

            special_params = [
                ('high_pitch_pct', 'High-pitch Percentage'),
                ('hyper_phonation_pct', 'Hyper-phonation Percentage'),
                ('voiced_pct', 'Voiced Percentage'),
                ('unvoiced_pct', 'Unvoiced Percentage')
            ]

            for param_key, param_label in special_params:
                if param_key in episode_stats:
                    value = episode_stats[param_key]
                    special_data.append([
                        param_label,
                        fmt(value)
                    ])

            if len(special_data) > 1:  # If we have data beyond headers
                special_table = Table(special_data, colWidths=[70*mm, 30*mm])
                special_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
                    ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')]),
                ]))

                elements.append(special_table)

            elements.append(Spacer(1, 12))

        return elements
