# 🍪 BiscuitAI — Real-Time Biscuit Quality Inspection System

AI-powered real-time defect detection for **Monaco**, **Parle-G**, and **Marie** biscuits.
Three specialized YOLOv8m models run in parallel on every camera frame.

---

## Tech Stack

| Layer       | Technology                                  |
|-------------|---------------------------------------------|
| Detection   | YOLOv8m (Ultralytics) — 3 separate models  |
| Backend     | Python 3.10+, Flask, Flask-SocketIO         |
| Frontend    | React 18, Recharts, Socket.IO client        |
| Database    | MySQL 8                                     |
| Auth / OTP  | SendGrid + JWT                              |
| OS          | Windows 10/11                               |

---

## Project Structure

```
biscuit_inspection/
├── .env                          # All credentials (fill this first)
├── requirements.txt              # Python deps
├── setup.bat                     # One-time setup
├── start_backend.bat             # Start Flask server
├── start_frontend.bat            # Start React dev server
├── start_all.bat                 # Launch both in separate windows
│
├── backend/
│   ├── app.py                    # Flask + SocketIO entry point
│   ├── routes/
│   │   ├── auth.py               # OTP login via SendGrid
│   │   ├── detection.py          # SocketIO camera/batch control
│   │   ├── batches.py            # Batch history API
│   │   ├── dashboard.py          # Analytics API
│   │   ├── export.py             # CSV export API
│   │   └── users.py              # Admin user management
│   ├── middleware/
│   │   └── auth_middleware.py    # JWT decorator
│   └── utils/
│       └── db.py                 # MySQL pool
│
├── testing/
│   └── detection_engine.py       # Multi-model inference engine
│
├── training/
│   ├── monaco/train_monaco.py
│   ├── parle/train_parle.py
│   └── marie/train_marie.py
│
├── frontend/
│   ├── public/index.html
│   ├── .env                      # REACT_APP_API_URL etc.
│   ├── package.json
│   └── src/
│       ├── index.js
│       ├── App.jsx               # Router + ProtectedRoute
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── utils/
│       │   ├── api.js            # Axios instance
│       │   └── socket.js         # Socket.IO singleton
│       ├── styles/
│       │   └── global.css
│       ├── components/
│       │   └── common/
│       │       └── Layout.jsx    # Sidebar shell
│       └── pages/
│           ├── HomePage.jsx      # Landing page
│           ├── FeaturesPage.jsx  # Features cards
│           ├── LoginPage.jsx     # OTP login
│           ├── DetectionPage.jsx # Live camera inspection
│           ├── DashboardPage.jsx # Analytics charts
│           └── HistoryPage.jsx   # Batch history + export
│
├── database/
│   └── schema.sql                # MySQL tables + stored procedure
│
├── models/                       # Place trained .pt files here
│   ├── monaco_best.pt
│   ├── parle_best.pt
│   └── marie_best.pt
│
├── dataset_zips/                 # Place Roboflow ZIPs here for training
│   ├── Monaco_v10i_yolov8.zip
│   ├── Parle_v5i_yolov8.zip
│   └── Marie_v5i_yolov8.zip
│
└── scripts/
    ├── add_user.py               # Add operators/admins to DB
    ├── test_camera.py            # Verify webcam before starting
    ├── test_models.py            # Verify .pt files load correctly
    └── train_all.py              # Run all 3 trainings in sequence
```

---

## Step-by-Step Setup

### Prerequisites
- Python 3.10 or 3.11 (3.12+ not tested with torch)
- Node.js 18+
- MySQL 8.0+
- Git
- A webcam

### 1. Clone / extract project

```bat
cd C:\Projects
REM extract the zip or clone here
cd biscuit_inspection
```

### 2. Fill `.env`

Open `.env` and set:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=biscuit_inspection
DB_USER=root
DB_PASSWORD=your_mysql_password

JWT_SECRET=some_long_random_string_here

SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_SENDER_EMAIL=noreply@biscuitai.com

CAMERA_INDEX=0
```

### 3. Run setup

```bat
setup.bat
```

This will:
- Create Python virtualenv
- Install all Python packages (`requirements.txt`)
- Run `npm install` in `frontend/`
- Import `database/schema.sql` into MySQL

### 4. Add your first user

```bat
call venv\Scripts\activate.bat
python scripts\add_user.py
```
Enter email, name, and role when prompted.

### 5. Train the models (skip if you already have `.pt` files)

Place Roboflow ZIPs in `dataset_zips/`:
- `Monaco_v10i_yolov8.zip`
- `Parle_v5i_yolov8.zip`
- `Marie_v5i_yolov8.zip`

Then train:
```bat
call venv\Scripts\activate.bat
python scripts\train_all.py
```

Training each model takes 1–4 hours depending on GPU.
Trained weights are automatically copied to `models/`.

### 6. Verify models

```bat
python scripts\test_models.py
```

### 7. Test camera

```bat
python scripts\test_camera.py
```
If camera doesn't open, try `--index 1`.
Update `CAMERA_INDEX` in `.env` accordingly.

### 8. Start the system

```bat
start_all.bat
```

Or in separate terminals:
```bat
REM Terminal 1
start_backend.bat

REM Terminal 2
start_frontend.bat
```

### 9. Open in browser

```
http://localhost:3000
```

---

## Inspection Workflow

1. **Home** → Read about the project
2. **Features** → Understand capabilities
3. **Sign In** → Enter email → receive OTP → enter OTP
4. **Detection page**:
   - Click **Start Camera**
   - Select brand (Monaco / Parle-G / Marie)
   - Click **Start Batch**
   - Place **2 biscuits** in front of the camera (side by side)
   - Detections appear with: `Brand | Quality | Confidence%`
   - Click **Stop Batch** when done
   - Click **Stop Camera**
5. **Dashboard** → View analytics, trends, defect rates
6. **History** → Browse all batches, click **View** for detail, export CSV

---

## Detection Logic

- All 3 models load at startup (no delay during batch)
- Every frame is sent to all 3 models **in parallel threads**
- Results from all models are merged; overlapping boxes (IoU > 0.4) keep highest confidence
- Heuristic filters reject non-biscuit objects:
  - Minimum area: 0.5% of frame
  - Maximum area: 60% of frame
  - Maximum aspect ratio: 3.5× (rejects hands/arms)
  - Minimum confidence: 55%
- **Stability buffer**: 3 consecutive frames must agree before a detection is logged
- Only logs when **exactly 2** biscuits are detected

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Camera won't open | Try `CAMERA_INDEX=1` in `.env` |
| Model not found | Check `models/` folder has `.pt` files |
| DB connection error | Verify MySQL is running, check `.env` credentials |
| OTP not received | Check `SENDGRID_API_KEY`, verify sender in SendGrid console |
| Detection too slow | Increase `FRAME_SKIP` in `.env` (e.g. `FRAME_SKIP=4`) |
| False detections | Increase `CONFIDENCE_THRESHOLD` to `0.65` in `.env` |
