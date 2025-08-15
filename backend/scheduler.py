from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from .tasks.weekly import run_weekly_job
from .config import Config

def start_scheduler(app):
    cfg = Config.from_env()
    try:
        tz = ZoneInfo(cfg.timezone)
    except Exception:
        tz = "UTC"

    sched = BackgroundScheduler(timezone=tz, job_defaults={"coalesce": True, "misfire_grace_time": 3600})
    trigger = CronTrigger(day_of_week="thu", hour=9, minute=0, timezone=tz)  # Thu 09:00 local
    sched.add_job(lambda: app.logger.info(f"[weekly_job] {run_weekly_job()}"),
                  trigger, id="weekly_pl_scrape", replace_existing=True)
    sched.start()
    app.logger.info("Scheduler started: Thursdays 09:00 local time")
    return sched

def main():
    from backend import create_app
    app = create_app()
    start_scheduler(app)  # should BLOCK (e.g., APScheduler BlockingScheduler.start())

if __name__ == "__main__":
    main()