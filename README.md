# WakeSnap 📸⏰

> An alarm app that won't stop until you photograph a random household object — proving you're actually out of bed.

---

## How It Works

1. Set an alarm time via the web UI
2. When the alarm fires, a random room object is chosen (lamp, mug, keyboard, etc.)
3. Your camera opens live with the challenge on screen
4. Point your camera at that object and tap **"This is it!"**
5. Google Vision AI verifies the photo — only then does the alarm stop ✅

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API** | FastAPI + Uvicorn | Alarm logic, photo verification, REST endpoints |
| **ORM / Admin** | Django 5 | Models, migrations, Django admin panel |
| **Database** | PostgreSQL (prod) / SQLite (local) | Persistent alarm & session storage |
| **Vision AI** | Google Cloud Vision API | Verifying the photographed object |
| **Static files** | WhiteNoise | Serving static assets in production |
| **Frontend** | Vanilla HTML / CSS / JS | Camera UI, alarm management |
| **Hosting** | Render | API + frontend + managed Postgres |

---

## Project Structure

```
wakesnap/
├── render.yaml                   ← Render Blueprint (provisions all services)
├── .gitignore
├── frontend/
│   └── index.html                ← Full web UI (camera, alarm setup, object pool)
└── backend/
    ├── fastapi_app.py            ← All FastAPI routes and Google Vision logic
    ├── alarm_scheduler.py        ← Background process: auto-triggers alarms by time
    ├── seed_data.py              ← Seeds 10 default room objects on first deploy
    ├── build.sh                  ← Render build script (migrate, collectstatic, seed)
    ├── requirements.txt          ← All Python dependencies
    ├── manage.py                 ← Django management CLI
    ├── core/
    │   ├── settings.py           ← Django settings (env-aware: SQLite local, Postgres prod)
    │   └── urls.py               ← Django URL config
    └── alarm_app/
        ├── models.py             ← Alarm, RoomObject, AlarmSession models
        ├── admin.py              ← Django admin configuration
        ├── serializers.py        ← DRF serializers
        ├── views.py              ← DRF views
        └── migrations/           ← Database migrations
```

---

## Data Models

### `RoomObject`
The pool of objects the alarm randomly picks from.

| Field | Type | Description |
|---|---|---|
| `name` | CharField | e.g. "Water Bottle" |
| `category` | CharField | furniture / electronics / kitchen / decor / other |
| `emoji` | CharField | e.g. "🫗" |
| `hint` | CharField | Shown to user during challenge |
| `is_active` | BooleanField | Toggle objects on/off without deleting |

### `Alarm`
A user-created alarm.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Auto-generated primary key |
| `label` | CharField | e.g. "Morning Hustle" |
| `time` | TimeField | HH:MM — when the alarm fires |
| `days` | JSONField | List of ints — 0=Mon, 6=Sun. Empty = fire once |
| `is_active` | BooleanField | Enable / disable the alarm |
| `snooze_count` | IntegerField | Tracks how many times snoozed |

### `AlarmSession`
Created each time an alarm fires.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Auto-generated |
| `alarm` | FK → Alarm | Which alarm triggered this |
| `assigned_object` | FK → RoomObject | The randomly chosen challenge object |
| `status` | CharField | pending / triggered / solved / snoozed / dismissed |
| `triggered_at` | DateTimeField | When the alarm fired |
| `solved_at` | DateTimeField | When the user successfully verified the photo |
| `photo_path` | CharField | Path to the saved verification photo |
| `ai_confidence` | FloatField | Score returned by Google Vision (0.0–1.0) |
| `ai_detected_label` | CharField | What Vision API detected in the photo |

---

## API Reference

Base URL local: `http://localhost:8000`
Base URL production: `https://wakesnap-api.onrender.com`

### Alarms

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/alarms` | List all active alarms |
| `POST` | `/alarms` | Create an alarm `{label, time, days}` |
| `PATCH` | `/alarms/{id}` | Update alarm (e.g. toggle `is_active`) |
| `DELETE` | `/alarms/{id}` | Deactivate an alarm |
| `POST` | `/alarms/trigger/{id}` | Manually trigger an alarm → returns challenge |

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions/{id}` | Get session status and assigned object |
| `POST` | `/sessions/{id}/verify` | Upload photo (multipart) to verify challenge |
| `POST` | `/sessions/{id}/snooze` | Snooze for 5 minutes |

### Room Objects

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/room-objects` | List all active room objects |
| `POST` | `/room-objects` | Add a new object to the pool |

### Utility

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns server time |
| `GET` | `/test-vision` | Tests your Google Vision API key with a dummy image |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Local Development

### Prerequisites

- Python 3.11+
- A Google Cloud project with **Cloud Vision API enabled**
- A Google Vision API key

### 1. Clone and set up

```bash
git clone https://github.com/YOUR_USERNAME/wakesnap.git
cd wakesnap/backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Create your `.env` file

Create `backend/.env`:

```env
GOOGLE_VISION_API_KEY=your_key_here
DEBUG=True
SECRET_KEY=any-random-string-for-local-dev
```

### 3. Set up the database and seed data

```bash
python manage.py migrate
python seed_data.py
```

### 4. Start the API server

```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open the frontend

```bash
cd ../frontend
python -m http.server 5500
# Open http://localhost:5500 in your browser
# Open https://wakesnap-frontend.onrender.com/ in production
```

### 6. (Optional) Run the alarm scheduler

In a separate terminal — this auto-triggers alarms when their set time is reached:

```bash
cd backend
python alarm_scheduler.py
```

---

## Deploying to Render

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/wakesnap.git
git push -u origin main
```

### Step 2 — Create a Blueprint deploy

1. Go to [render.com](https://render.com) and sign in
2. Click **New → Blueprint**
3. Connect your GitHub repository
4. Render finds `render.yaml` automatically and previews what it will create:
   - `wakesnap-api` — Python web service (FastAPI + Django)
   - `wakesnap-frontend` — Static site (HTML frontend)
   - `wakesnap-db` — Free managed PostgreSQL database
5. Click **Apply**

The PostgreSQL `DATABASE_URL` is automatically injected into the API service via `render.yaml` — no manual copy-pasting needed.

```yaml
# How the DB is wired in render.yaml:
databases:
  - name: wakesnap-db       # ← Render creates this Postgres instance

services:
  - name: wakesnap-api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: wakesnap-db  # ← auto-injects the connection string here
```

Django's `settings.py` reads it automatically:

```python
if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.config(default=DATABASE_URL)}
else:
    DATABASES = {"default": {"ENGINE": "sqlite3", ...}}  # local fallback
```

### Step 3 — Add your Google Vision API key

`GOOGLE_VISION_API_KEY` is intentionally excluded from `render.yaml` (marked `sync: false`) so it's never committed to Git. Add it manually:

1. Render dashboard → **wakesnap-api** service → **Environment** tab
2. Add: `GOOGLE_VISION_API_KEY` = your key
3. Click **Save Changes** — Render auto-redeploys

### Step 4 — Verify everything is working

```
https://wakesnap-api.onrender.com/health       ← should return {"status":"ok"}
https://wakesnap-api.onrender.com/test-vision  ← should return {"status":"Vision API OK"}
https://wakesnap-api.onrender.com/docs         ← Swagger UI
```

### Step 5 — Open the frontend

Your frontend is live at:
```
https://wakesnap-frontend.onrender.com
```

---

## Environment Variables

| Variable | Required | Set by | Description |
|---|---|---|---|
| `GOOGLE_VISION_API_KEY` | Yes | You (manually) | Google Cloud Vision API key |
| `SECRET_KEY` | Yes | Render (auto-generated) | Django secret key |
| `DATABASE_URL` | Yes (prod) | Render (auto-injected) | PostgreSQL connection string |
| `DEBUG` | No | render.yaml | `"False"` in prod, `"True"` locally |
| `DJANGO_SETTINGS_MODULE` | Yes | render.yaml | Always `core.settings` |

---

## How Vision Verification Works

When a photo is submitted to `POST /sessions/{id}/verify`:

1. The image bytes are read from the upload
2. They're base64-encoded and sent to Google Cloud Vision **Label Detection**
3. Vision returns a ranked list of detected labels with confidence scores (0.0–1.0)
4. The app checks if the **target object's name** appears in any returned label
5. A match with score ≥ **0.65** dismisses the alarm ✅
6. No match → user is shown "Try again" and the camera reopens

```
Photo of shoes
  → Vision detects: ["Footwear" 0.97, "Shoe" 0.95, "Sneaker" 0.88]
  → Target: "Shoes"
  → "shoe" in "Shoe" with score 0.95 ≥ 0.65 → ✅ Alarm dismissed
```

---

## Django Admin Panel

Manage alarms, room objects, and session history through Django's built-in admin.

**Locally:**
```bash
cd backend
python manage.py createsuperuser
python manage.py runserver 8001
# Open http://localhost:8001/admin
```

**On Render:**
```bash
# Render dashboard → wakesnap-api → Shell tab
python manage.py createsuperuser
# Then open https://wakesnap-api.onrender.com/admin
```

---

## Known Limitations & Future Improvements

| Limitation | Suggested Fix |
|---|---|
| Alarm photos reset on redeploy (ephemeral disk) | Integrate **Cloudinary** or **AWS S3** |
| Free Render tier sleeps after 15 min of inactivity | Ping `/health` every 10 min via a cron service, or upgrade plan |
| Vision threshold is hardcoded at 0.65 | Make it configurable per alarm or room object |
| No user accounts — alarms are global | Add Django auth + per-user alarm isolation |
| Alarm scheduler is a separate manual process | Move to **Celery + Redis** for reliable scheduling |

---

## License

MIT
