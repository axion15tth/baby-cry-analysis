from celery import Celery
from app.config import settings

celery_app = Celery(
    "baby_cry_analysis",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analysis_tasks"]
)

# Celery設定
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 12,  # 12時間のタイムリミット
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
)
