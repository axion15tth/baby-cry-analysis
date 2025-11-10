from functools import wraps
from typing import Callable
from fastapi import HTTPException, status
from app.models.user import User


def require_researcher(func: Callable) -> Callable:
    """
    研究者権限が必要なエンドポイント用デコレータ

    Usage:
        @router.get("/some-endpoint")
        @require_researcher
        async def some_endpoint(current_user: User = Depends(get_current_user)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # current_userを引数から取得
        current_user = kwargs.get('current_user')
        if not current_user:
            # 引数から探す
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です"
            )

        if current_user.role != "researcher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この機能は研究者アカウントのみ利用可能です"
            )

        return await func(*args, **kwargs)

    return wrapper


def check_researcher(user: User) -> bool:
    """
    ユーザーが研究者かどうかをチェック

    Args:
        user: ユーザーオブジェクト

    Returns:
        研究者ならTrue、そうでなければFalse
    """
    return user.role == "researcher"


def check_file_access(user: User, file_user_id: int) -> bool:
    """
    ユーザーがファイルにアクセスできるかチェック

    Args:
        user: ユーザーオブジェクト
        file_user_id: ファイルの所有者ID

    Returns:
        アクセス可能ならTrue、そうでなければFalse
    """
    # 研究者は全ファイルにアクセス可能
    if user.role == "researcher":
        return True

    # 一般ユーザーは自分のファイルのみアクセス可能
    return user.id == file_user_id


def ensure_file_access(user: User, file_user_id: int):
    """
    ファイルアクセス権限を確認し、アクセスできない場合は例外を発生

    Args:
        user: ユーザーオブジェクト
        file_user_id: ファイルの所有者ID

    Raises:
        HTTPException: アクセスできない場合
    """
    if not check_file_access(user, file_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このファイルへのアクセス権限がありません"
        )
