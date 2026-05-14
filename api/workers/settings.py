"""
ARQ WorkerSettings — lists all jobs and cron schedules.
"""
from __future__ import annotations
from arq import cron
from arq.connections import RedisSettings
from api.core.config import settings
from api.workers.inbound import process_inbound_message
from api.workers.briefing import send_morning_briefing
from api.workers.polls import poll_rss_feeds, poll_reddit, poll_hn, poll_github
from api.workers.markets import poll_stocks, poll_crypto
from api.workers.followup import check_followup_nudges, check_single_followup
from api.workers.alerts import check_price_alerts, check_keyword_alerts

_hour = int(settings.briefing_time.split(":")[0]) if ":" in settings.briefing_time else 8
_minute = int(settings.briefing_time.split(":")[1]) if ":" in settings.briefing_time else 0

class WorkerSettings:
    functions = [
        process_inbound_message,
        check_single_followup,
    ]
    cron_jobs = [
        cron(send_morning_briefing, hour={_hour}, minute={_minute}),
        cron(poll_rss_feeds, minute={0, 30}),
        cron(poll_reddit, minute={15, 45}),
        cron(poll_hn, hour={7, 12, 18}),
        cron(poll_github, minute={10}),
        cron(poll_stocks, hour={9, 12, 15, 18}),
        cron(poll_crypto, minute={5}),
        cron(check_followup_nudges, hour={8}),
        cron(check_price_alerts, hour={9, 15, 21}),
        cron(check_keyword_alerts, minute={20, 50}),
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 60
