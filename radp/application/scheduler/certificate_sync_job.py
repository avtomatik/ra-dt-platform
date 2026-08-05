from apscheduler.schedulers.background import BackgroundScheduler

from radp.bootstrap.runtime import get_runtime


def start_scheduler() -> None:
    runtime = get_runtime()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        runtime.synchronization.synchronize, trigger="cron", hour=2, minute=0
    )
    scheduler.start()
