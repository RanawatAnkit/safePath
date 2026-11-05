# 🛡️ SafePath — Crime-Aware Safe Route & Personal Safety App

SafePath is a Flask web application that helps people travel more safely. It visualises crime hotspots on an interactive map, predicts a **0–10 crime risk score** for any location using a **Random Forest** model, ranks real road routes by crime exposure, and provides an **SOS alert** that sends your live location to an emergency contact by SMS.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗺️ **Crime Map** | Crime incidents plotted on a Leaflet map, colour-coded by severity, with radius / limit filters |
| 🤖 **Risk Prediction** | ML model (RandomForestRegressor) predicts risk for your current location → Low / Medium / High |
| 🛣️ **Safe Route Finder** | Fetches alternative routes from OSRM and scores each by nearby crimes (inverse-distance weighting); routes shown green / yellow / red |
| 🆘 **SOS Alert** | One click sends an SMS via Twilio with a Google Maps link to your location; alerts can be tracked and resolved |
| 📝 **Crime Reporting** | Users report incidents with location (GPS + reverse geocoding) and optional evidence upload |
| 🏥 **Safe Places** | Find nearby police stations, hospitals, fire stations, banks, schools and government offices |
| 📊 **Statistics** | Crime counts by type, average severity, hourly distribution and 30-day trend |
| 🔐 **Authentication** | Register / login (username or email) with hashed passwords and emergency contact details |

---

## 🧰 Tech Stack

- **Backend:** Python 3.11, Flask, Flask-SQLAlchemy, Flask-Login
- **Database:** SQLite (PostgreSQL-ready via `DATABASE_URL`)
- **Machine Learning:** scikit-learn, pandas, NumPy, joblib
- **Frontend:** Jinja2, Bootstrap 5, Leaflet.js, Leaflet Routing Machine, Font Awesome, vanilla JavaScript
- **External APIs:** OSRM (routing), Nominatim / OpenStreetMap (geocoding & tiles), Twilio (SMS)

---

## 🏗️ Architecture

```
Browser (Leaflet map + Bootstrap UI)
   │  fetch() JSON / multipart
   ▼
Flask (routes.py) ──► crime_predictor.py (Random Forest, saved as .pkl)
   │
   ▼
SQLAlchemy models ──► SQLite (instance/safepath.db)
   │
   ├──► OSRM API      – alternative routes
   ├──► Twilio API    – SOS SMS
   └──► Nominatim     – geocoding (from browser)
```

---

## 📁 Project Structure

```
safePath/
├── app.py                    # Flask app, DB & login manager setup
├── main.py                   # Entry point (runs on port 5000)
├── models.py                 # User, CrimeData, SafeRoute, SOSAlert, SafePlace
├── routes.py                 # Pages and REST API endpoints
├── crime_predictor.py        # ML training, loading and risk prediction
├── safe_places_generator.py  # Seeds sample safe places
├── update_datasets.py        # Imports crime data from CSV
├── migrate_db.py             # Adds crime-report columns to an old DB
├── crime_model.pkl           # Trained Random Forest model
├── crime_encoder.pkl         # Crime-type label encoder
├── datasets/
│   ├── maharashtra_crime_dataset.csv
│   └── safe_place.csv
├── static/
│   ├── css/style.css
│   ├── js/map.js             # Map, routes, safe places, SOS, reporting
│   ├── js/crime-predictor.js # Risk panel and statistics
│   └── evidence/             # Uploaded evidence files
└── templates/
    ├── base.html, index.html, profile.html
    └── auth/login.html, auth/register.html
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Internet connection (map tiles, routing and geocoding use online services)
- A [Twilio](https://www.twilio.com/) account (only needed for SOS SMS)

### Installation

```bash
git clone https://github.com/RanawatAnkit/safePath.git
cd safePath

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install flask flask-sqlalchemy flask-login scikit-learn pandas numpy joblib requests twilio werkzeug email-validator
```

### Configuration (optional)

| Variable | Default | Purpose |
|---|---|---|
| `SESSION_SECRET` | dev key | Flask session secret |
| `DATABASE_URL` | `sqlite:///safepath.db` | Database connection string |

Twilio credentials (`ACCOUNT_SID`, `AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`) are configured at the top of `routes.py`.
> Note: Twilio trial accounts can only send SMS to verified numbers.

### Run

```bash
python main.py
```

Open **http://localhost:5000** and allow location access when prompted.

On first start the app creates the database tables and seeds safe places automatically. The ML model is loaded from `crime_model.pkl`; if missing, it is retrained from the crime data in the database.

---

## 🤖 How the Risk Model Works

1. **Features (8):** latitude, longitude, hour, day of week, month, day, encoded crime type, severity.
2. **Target:** crimes are grouped into ~110 m grid cells (coordinates rounded to 3 decimals) and scored as
   `risk = 0.7 × mean_severity + 0.3 × (count / max_count) × 10`.
3. **Model:** `RandomForestRegressor(n_estimators=100)` with an 80/20 train-test split, saved with joblib.
4. **Prediction:** local stats within ~1 km (bounding box: `Δlat = r/111`, `Δlng = r/(111·cos lat)`) feed the model; output is clamped to 0–10.
   **≥ 7 → High · ≥ 4 → Medium · else Low**

## 🛣️ How Safe Routing Works

1. Source and destination are geocoded with Nominatim.
2. OSRM returns multiple alternative road routes (GeoJSON).
3. For every point on a route: `risk = Σ severity / (distance + 1)` over crimes within **200 m** (Haversine distance).
4. Route risk = average point risk; routes are normalised against each other and drawn **green → yellow → red**.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in (username or email) |
| POST | `/api/auth/logout` | Log out |
| GET | `/api/auth/status` | Current login status |
| POST | `/api/current-location-risk` | Risk score + area stats for a location |
| GET | `/api/crime-data` | Crimes near a location (`lat`, `lng`, `radius`, `limit`) |
| GET | `/api/crime-stats` | Aggregate crime statistics |
| POST | `/get_routes` | Alternative routes with risk scores |
| POST | `/api/safe-route` | Legacy waypoint-based safe route |
| POST | `/api/sos/alert` | Send SOS SMS (login required) |
| GET | `/api/sos/alerts` | List your SOS alerts |
| POST | `/api/sos/alert/<id>/resolve` | Resolve an SOS alert |
| GET | `/api/safe-places` | Nearby safe places (`lat`, `lng`, `radius`, `type`) |
| GET | `/api/safe-places/types` | Available safe place types |
| POST | `/api/report-crime` | Submit a crime report with evidence |
| GET | `/api/my-reports` | Your submitted reports |

---

## 🔮 Future Improvements

- Admin dashboard to verify user-submitted reports
- Time-aware routing (day vs night risk)
- Spatial indexing (PostGIS / KD-tree) for faster route scoring
- Live location sharing during a trip
- Database migrations with Alembic
- Mobile app / PWA

---

## 👤 Author

**Ankit Ranawat** — [GitHub](https://github.com/RanawatAnkit)
