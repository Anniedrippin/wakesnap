import os, sys, time, requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from alarm_app.models import Alarm, AlarmSession

FASTAPI_BASE = "http://localhost:8000"


def check_and_trigger():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = now.weekday()  # 0=Mon

    alarms = Alarm.objects.filter(is_active=True)
    for alarm in alarms:
        alarm_time = str(alarm.time)[:5]
        if alarm_time != current_time:
            continue
        if alarm.days and current_day not in alarm.days:
            continue

        # Check not already triggered this minute
        already = AlarmSession.objects.filter(
            alarm=alarm,
            status__in=["triggered", "solved"],
            triggered_at__date=now.date(),
        ).exists()

        if already:
            continue

        print(f"[{now.strftime('%H:%M:%S')}] 🚨 Triggering alarm: {alarm.label}")
        try:
            r = requests.post(f"{FASTAPI_BASE}/alarms/trigger/{alarm.id}")
            data = r.json()
            print(f"  → Challenge: {data.get('object_emoji')} {data.get('object_name')}")
            print(f"  → Session: {data.get('session_id')}")
        except Exception as e:
            print(f"  → Error triggering: {e}")


if __name__ == "__main__":
    print("🕐 WakeSnap Scheduler running — checking every 30s")
    while True:
        check_and_trigger()
        time.sleep(30)