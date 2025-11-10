from datetime import datetime, timedelta
from typing import Optional


def seconds_to_absolute_time(
    recording_start_time: Optional[datetime],
    relative_seconds: float
) -> Optional[datetime]:
    """
    相対時刻（秒）を絶対時刻に変換

    Args:
        recording_start_time: 録音開始時刻（絶対時刻）
        relative_seconds: 相対時刻（秒）

    Returns:
        絶対時刻、recording_start_timeがNoneの場合はNone
    """
    if recording_start_time is None:
        return None

    return recording_start_time + timedelta(seconds=relative_seconds)


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S.%f") -> str:
    """
    日時をフォーマット

    Args:
        dt: 日時オブジェクト
        format_str: フォーマット文字列

    Returns:
        フォーマットされた文字列、dtがNoneの場合は空文字列
    """
    if dt is None:
        return ""

    # ミリ秒まで表示（マイクロ秒の最初の3桁）
    formatted = dt.strftime(format_str)
    if ".%f" in format_str:
        # マイクロ秒をミリ秒に変換（6桁→3桁）
        formatted = formatted[:-3]

    return formatted


def format_seconds(seconds: float, decimals: int = 3) -> str:
    """
    秒数をフォーマット

    Args:
        seconds: 秒数
        decimals: 小数点以下の桁数

    Returns:
        フォーマットされた文字列
    """
    return f"{seconds:.{decimals}f}"


def seconds_to_time_string(seconds: float) -> str:
    """
    秒数を時:分:秒.ミリ秒形式に変換

    Args:
        seconds: 秒数

    Returns:
        HH:MM:SS.mmm形式の文字列
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
