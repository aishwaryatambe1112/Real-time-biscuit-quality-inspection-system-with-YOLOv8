# 🍪 BiscuitAI — Real-Time Biscuit Quality Inspection System
> AI-Powered Multi-Model Defect Detection for Food Manufacturing

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **AI / ML** | Python 3.10+, YOLOv8m (Ultralytics) | Core inference engine, 3 brand-specific detection models |
| **Backend** | Flask, Flask-SocketIO | REST API server + real-time WebSocket frame streaming |
| **Frontend** | React.js 18, JavaScript, HTML5, CSS3 | Live camera feed UI, dashboard, batch management |
| **Charts** | Recharts | Analytics dashboard — defect trends, brand comparisons |
| **Database** | MySQL 8.0 | Batch-wise detection history, hourly stats, user data |
| **Auth** | SendGrid (OTP email), JWT | Passwordless login via one-time passcode |
| **Camera** | DroidCam (Android app + PC client) | Use phone as high-quality WiFi webcam |
| **Dataset** | Roboflow | Image annotation, augmentation, YOLOv8 export |
| **Dev Tools** | Node.js (npm), Git | Frontend package management, version control |

---

## 📖 Table of Contents

1. [Project Overview](#-project-overview)
2. [How It Works](#-how-it-works)
3. [System Architecture](#-system-architecture)
4. [Camera Setup — DroidCam](#-camera-setup--droidcam-phone-as-webcam)
5. [Folder Structure](#-folder-structure)
6. [Prerequisites](#-prerequisites)
7. [Account Setup](#-account-setup-sendgrid--mysql)
8. [Installation — Windows](#-installation--windows)
9. [Installation — macOS](#-installation--macos)
10. [Environment Variables (.env)](#-environment-variables-env-file)
11. [Database Setup](#-database-setup)
12. [Adding Your Login Email](#-adding-your-login-email-to-database)
13. [Dataset Download & Model Training](#-dataset-download--model-training)
14. [Running the Project](#-running-the-project)
15. [Using the System](#-using-the-system)

---

## 🎯 Project Overview

The **Real-Time Biscuit Quality Inspection System** is a production-grade AI application that uses deep learning to automatically detect and classify biscuit defects from a live camera feed — replacing slow, unreliable manual inspection on production lines.

### What It Does
- Detects biscuits in real-time from a webcam or DroidCam phone camera
- Classifies each biscuit as **Good ✅**, **Broken ❌**, or **Burnt 🔥**
- Supports 3 biscuit brands: **Monaco**, **Parle-G**, **Marie**
- Logs every confirmed detection to a **MySQL database** batch-wise
- Displays live analytics on a **React dashboard**
- Exports history as **CSV files**

### Why This Matters
> Manual inspection on high-speed biscuit lines misses up to 15% of defects due to human fatigue. A single production line processes 800–1,200 biscuits per minute — impossible to inspect individually. This system provides AI-grade inspection deployable with just a phone camera and a standard PC.

---

## ⚙️ How It Works

```
Phone (DroidCam) ──WiFi──► Laptop (DroidCam Client)
                                    │
                                    ▼
                          CamCapture Thread (30fps)
                           /                    \
                    _raw_q queue           _infer_q queue
                         │                        │
                  FramePush Thread         Inference Thread
                         │                        │
                  JPEG encode              Run selected brand's
                         │                YOLOv8m model ONLY
                  SocketIO emit                   │
                         │                Heuristic Filter
                         ▼                (confidence, area,
                   React Browser           aspect ratio)
                   Live Camera Feed               │
                                         Stability Buffer
                                        (3 frames must agree)
                                                  │ YES
                                                  ▼
                                          MySQL Database
                                       (detections, batches)
                                                  │
                                                  ▼
                                         React Dashboard
                                       (charts, history, CSV)
```

### Key Design Decisions

| Decision | Reason |
|----------|--------|
| **3 separate YOLOv8m models** | Combined training caused cross-brand confusion. Separate models = brand-specific feature learning |
| **Only selected brand's model runs** | Prevents false labels from other brand models appearing on wrong biscuit |
| **Stability buffer (3 frames)** | Eliminates single-frame false positives (hands, faces, backgrounds) |
| **Python threading** | Separates camera capture, display push, and inference so none blocks the other |
| **DroidCam phone camera** | Laptop webcams are low quality. Phone camera provides HD clarity needed for small biscuit defect detection |
| **YOLOv8m over YOLOv8n/s** | Broken biscuits have irregular shapes. YOLOv8m's deeper features detect irregular objects better |

---

## 🏗️ System Architecture

```
C:\Real-time biscuit quality inspection system with YOLOv8\
│
├── 📄 .env                          ← All secrets & config (YOU FILL THIS)
├── 📄 requirements.txt              ← Python dependencies
├── 📄 detection.py                  ← Standalone detection route (root level copy)
├── 📄 setup.bat                     ← Windows: installs everything
├── 📄 start_all.bat                 ← Windows: starts backend + frontend
├── 📄 start_backend.bat             ← Starts Flask backend only
├── 📄 start_frontend.bat            ← Starts React frontend only
├── 📄 README.md
│
├── 📁 backend\
│   ├── __init__.py
│   ├── app.py                       ← Flask + SocketIO entry point
│   ├── 📁 routes\
│   │   ├── __init__.py
│   │   ├── auth.py                  ← OTP login via SendGrid
│   │   ├── detection.py             ← Camera + batch control endpoints
│   │   ├── batches.py               ← Batch history endpoints
│   │   ├── dashboard.py             ← Analytics data endpoints
│   │   ├── export.py                ← CSV export endpoint
│   │   └── users.py                 ← User management
│   ├── 📁 middleware\
│   │   ├── __init__.py
│   │   └── auth_middleware.py       ← JWT token verification
│   └── 📁 utils\
│       ├── __init__.py
│       └── db.py                    ← MySQL connection & schema init
│
├── 📁 testing\
│   ├── __init__.py
│   └── detection_engine.py          ← Multi-threaded YOLOv8 inference engine
│
├── 📁 models\                       ← TRAINED .pt FILES GO HERE (after training)
│   ├── monaco_best.pt               ← copy from training\monaco\runs\...\weights\best.pt
│   ├── parle_best.pt                ← copy from training\parle\runs\...\weights\best.pt
│   └── marie_best.pt                ← copy from training\marie\runs\...\weights\best.pt
│
├── 📁 database\
│   └── schema.sql                   ← MySQL tables & stored procedures
│
├── 📁 dataset_zips\                 ← PASTE DOWNLOADED DATASET ZIPS HERE
│   ├── Monaco_v10i_yolov8.zip       ← downloaded from Google Drive link below
│   ├── Parle_v5i_yolov8.zip
│   └── Marie_v5i_yolov8.zip
│
├── 📁 training\                     ← Training scripts — one per brand
│   ├── 📁 monaco\
│   │   ├── 📁 dataset\              ← Extract Monaco zip here
│   │   │   ├── train\images\ + labels\
│   │   │   ├── valid\images\ + labels\
│   │   │   ├── test\images\ + labels\
│   │   │   ├── data.yaml            ← Roboflow dataset config
│   │   │   └── README.roboflow
│   │   ├── 📁 runs\                 ← Auto-created by YOLOv8 after training
│   │   │   └── monaco_YYYYMMDD\weights\best.pt  ← Copy to models\monaco_best.pt
│   │   ├── train_monaco.py          ← Run this to train Monaco model
│   │   ├── yolo26n.pt               ← YOLOv8 nano base weights
│   │   └── yolov8m.pt               ← YOLOv8 medium base weights (used for training)
│   ├── 📁 parle\
│   │   ├── 📁 dataset\              ← Extract Parle zip here
│   │   ├── 📁 runs\
│   │   ├── train_parle.py
│   │   ├── yolo26n.pt
│   │   └── yolov8m.pt
│   └── 📁 marie\
│       ├── 📁 dataset\              ← Extract Marie zip here
│       ├── 📁 runs\
│       ├── train_marie.py
│       ├── yolo26n.pt
│       └── yolov8m.pt
│
├── 📁 exports\                      ← CSV exports saved here (auto-created)
│
├── 📁 venv\                         ← Python virtual environment (auto-created)
│
├── 📁 scripts\
│   ├── add_user.py                  ← Add login email to database
│   ├── test_camera.py               ← Verify camera works
│   ├── test_models.py               ← Verify all 3 models load
│   └── train_all.py                 ← Runs all 3 training scripts in sequence
│
└── 📁 frontend\
    ├── .env                         ← Frontend env (API URL)
    ├── package.json
    ├── 📁 public\
    │   └── index.html
    └── 📁 src\
        ├── index.js
        ├── App.jsx
        ├── 📁 context\
        │   └── AuthContext.jsx      ← JWT auth state
        ├── 📁 utils\
        │   ├── api.js               ← Axios API calls
        │   └── socket.js            ← SocketIO client
        ├── 📁 styles\
        │   └── global.css
        ├── 📁 components\
        │   └── common\
        │       └── Layout.jsx
        └── 📁 pages\
            ├── HomePage.jsx         ← Landing / about
            ├── FeaturesPage.jsx     ← Feature cards
            ├── LoginPage.jsx        ← OTP login
            ├── DetectionPage.jsx    ← Live camera + detection
            ├── DashboardPage.jsx    ← Analytics charts
            └── HistoryPage.jsx      ← Batch history + CSV export
```

---

## 📱 Camera Setup — DroidCam (Phone as Webcam)

> This project uses **DroidCam** to use your phone's camera instead of a laptop webcam. Phone cameras provide much higher resolution and image quality — critical for detecting small defects on biscuits.

### Setup Steps

**On your Android Phone:**
1. Install **DroidCam** from Google Play Store (free)
2. Open the app — note the **WiFi IP address** shown (e.g., `192.168.1.5`)
3. Keep the app open and phone screen on

**On your Windows Laptop:**
1. Download & install **DroidCam Windows Client** from [dev47apps.com](https://www.dev47apps.com/)
2. Open DroidCam client
3. Enter the IP address shown on your phone
4. Port: `4747` (default)
5. Click **Connect**
6. DroidCam now appears as a webcam (`DroidCam Source`) in your system

**Physical Setup:**
- Mount your phone on a **tripod** facing downward
- Place biscuits on a **white chart paper** laid flat below
- Arrange biscuits in **2 per row** with clear spacing between rows
- Ensure good lighting (avoid harsh shadows)

**In `.env` file:**
```env
CAMERA_INDEX=1   # DroidCam usually registers as index 1
                 # If it doesn't work, try 0 or 2
```

**Test the camera:**
```cmd
python scripts\test_camera.py
# If blank, try:
python scripts\test_camera.py --index 1
python scripts\test_camera.py --index 2
```

---

## ✅ Prerequisites

### Software to Install

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.10 or 3.11 | [python.org](https://python.org/downloads) |
| Node.js | 18+ LTS | [nodejs.org](https://nodejs.org) |
| MySQL Server | 8.0 | [mysql.com](https://dev.mysql.com/downloads/mysql/) |
| MySQL Workbench | Any | [mysql.com](https://dev.mysql.com/downloads/workbench/) (optional, easier DB management) |
| Git | Latest | [git-scm.com](https://git-scm.com) |
| DroidCam Client | Latest | [dev47apps.com](https://www.dev47apps.com/) |

> ⚠️ During Python install on Windows — check **"Add Python to PATH"** before clicking Install.

> ⚠️ During MySQL install — note the **root password** you set. You'll need it in `.env`.

---

## 🔑 Account Setup: SendGrid & MySQL

### SendGrid (for OTP email)

SendGrid sends the OTP code to your email when you log in. Without this, login will not work.

1. Go to [sendgrid.com](https://sendgrid.com) → **Sign Up** (free tier is enough)
2. After signup → **Email API** → **Integration Guide** → **SMTP** or **Web API**
3. Go to **Settings** → **API Keys** → **Create API Key**
4. Give it a name: `BiscuitAI`
5. Select **Full Access** → **Create & View**
6. **Copy the API key** (starts with `SG.`) — you only see it once!
7. Go to **Settings** → **Sender Authentication** → **Single Sender Verification**
8. Add and verify your email address (e.g., `yourname@gmail.com`)
9. This verified email is your `SENDGRID_SENDER_EMAIL` in `.env`

```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_SENDER_EMAIL=yourname@gmail.com     ← must be verified on SendGrid
SENDGRID_SENDER_NAME=BiscuitAI System
```

> 💡 During development: if OTP email doesn't arrive, check the **backend terminal** — the OTP is printed there as a fallback.

---

## 💻 Installation — Windows

### Step 1 — Clone the Repository

Open **Command Prompt** (`Win + R` → type `cmd` → Enter):

```cmd
cd C:\
git clone https://github.com/YOUR_USERNAME/biscuit-quality-inspection.git "Real-time biscuit quality inspection system with YOLOv8"
cd "Real-time biscuit quality inspection system with YOLOv8"
```

> Or manually download the ZIP and extract to:
> `C:\Real-time biscuit quality inspection system with YOLOv8\`

### Step 2 — Create Python Virtual Environment

```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"

python -m venv venv

venv\Scripts\activate
```

You should see `(venv)` at the start of your command line. This means the virtual environment is active.

> ⚠️ **Every time you open a new CMD window**, you must run `venv\Scripts\activate` again before running any Python command.

### Step 3 — Create Required Empty Folders & __init__.py Files

```cmd
mkdir models
mkdir exports

type nul > backend\__init__.py
type nul > backend\routes\__init__.py
type nul > backend\middleware\__init__.py
type nul > backend\utils\__init__.py
type nul > testing\__init__.py
```

### Step 4 — Fill in the .env File

Open `C:\Real-time biscuit quality inspection system with YOLOv8\.env` in Notepad and fill every value:

```env
# ── Database ────────────────────────────────────────────
DB_HOST=localhost
DB_PORT=3306
DB_NAME=biscuit_inspection
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_ROOT_PASSWORD_HERE    ← the password you set during MySQL install

# ── Auth ────────────────────────────────────────────────
JWT_SECRET=biscuitai_super_secret_key_2025_change_this_to_something_random

# ── SendGrid ────────────────────────────────────────────
SENDGRID_API_KEY=SG.your_key_here
SENDGRID_SENDER_EMAIL=yourname@gmail.com     ← must be verified on SendGrid
SENDGRID_SENDER_NAME=BiscuitAI System

# ── Server ──────────────────────────────────────────────
BACKEND_PORT=5000
FRONTEND_PORT=3000

# ── Model Paths ─────────────────────────────────────────
MONACO_MODEL_PATH=models/monaco_best.pt
PARLE_MODEL_PATH=models/parle_best.pt
MARIE_MODEL_PATH=models/marie_best.pt

# ── Detection Config ────────────────────────────────────
CONFIDENCE_THRESHOLD=0.25
IOU_THRESHOLD=0.45
CAMERA_INDEX=1                               ← 0 = laptop webcam, 1 = DroidCam
FRAME_SKIP=2
```

### Step 5 — Install Python Packages

```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"
venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

> This takes 5–15 minutes on first run (downloads PyTorch, Ultralytics YOLOv8, Flask, etc.)

### Step 6 — Install Frontend Packages

```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8\frontend"
npm install
cd ..
```

> This takes 2–5 minutes.

### Step 7 — Copy Your Trained Models

After training, YOLOv8 saves `best.pt` inside a timestamped folder. Find and copy all 3:

```cmd
REM List your training runs to find the folder names:
dir training\monaco\runs\
dir training\parle\runs\
dir training\marie\runs\

REM Copy best.pt files (replace timestamps with yours):
copy training\monaco\runs\monaco_20250101_120000\weights\best.pt models\monaco_best.pt
copy training\parle\runs\parle_20250101_120000\weights\best.pt   models\parle_best.pt
copy training\marie\runs\marie_20250101_120000\weights\best.pt   models\marie_best.pt
```

After copying, verify:
```cmd
dir models\
```
Expected:
```
monaco_best.pt
parle_best.pt
marie_best.pt
```

---

## 🍎 Installation — macOS

> The project works on macOS with minor path differences.

### Step 1 — Clone the Repository

Open **Terminal**:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/biscuit-quality-inspection.git "Real-time biscuit quality inspection system with YOLOv8"
cd "Real-time biscuit quality inspection system with YOLOv8"
```

### Step 2 — Install Prerequisites (if not already installed)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Node.js
brew install node

# Install MySQL
brew install mysql
brew services start mysql

# Set MySQL root password
mysql_secure_installation
```

### Step 3 — Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

> On macOS, use `source venv/bin/activate` instead of `venv\Scripts\activate`

### Step 4 — Create Required Files

```bash
mkdir -p models exports

touch backend/__init__.py
touch backend/routes/__init__.py
touch backend/middleware/__init__.py
touch backend/utils/__init__.py
touch testing/__init__.py
```

### Step 5 — Fill .env

Same content as Windows. Open with:
```bash
nano .env
# or
open -a TextEdit .env
```

### Step 6 — Install Packages

```bash
# Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Frontend packages
cd frontend && npm install && cd ..
```

### Step 7 — Copy Trained Models

```bash
cp training/monaco/runs/monaco_*/weights/best.pt models/monaco_best.pt
cp training/parle/runs/parle_*/weights/best.pt   models/parle_best.pt
cp training/marie/runs/marie_*/weights/best.pt   models/marie_best.pt
```

---

## 🗃️ Database Setup

### Step 1 — Start MySQL

**Windows:**
```cmd
REM MySQL usually auto-starts. Check via:
services.msc
REM Find "MySQL80" → right-click → Start
```

**macOS:**
```bash
brew services start mysql
```

### Step 2 — Create the Database

**Windows:**
```cmd
mysql -u root -p
```
Enter your MySQL root password, then:
```sql
CREATE DATABASE IF NOT EXISTS biscuit_inspection;
EXIT;
```

**macOS:**
```bash
mysql -u root -p
```
Same SQL commands above.

### Step 3 — Import the Schema

**Windows:**
```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"
mysql -u root -p biscuit_inspection < database\schema.sql
```

**macOS:**
```bash
cd ~/Real-time\ biscuit\ quality\ inspection\ system\ with\ YOLOv8
mysql -u root -p biscuit_inspection < database/schema.sql
```

Enter password when prompted. No errors = success.

---

## 👤 Adding Your Login Email to Database

The system uses OTP-based login — no passwords stored. You must add your email to the database first.

**Windows:**
```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"
venv\Scripts\activate
python scripts\add_user.py
```

**macOS:**
```bash
cd ~/Real-time\ biscuit\ quality\ inspection\ system\ with\ YOLOv8
source venv/bin/activate
python scripts/add_user.py
```

It will prompt:
```
Enter email    : yourname@gmail.com
Enter name     : Your Name
Role (operator/admin) [operator]: admin
```

> ⚠️ The email you enter here **must match** the email you verify on SendGrid — otherwise OTP emails won't send.

To add more users, run the script again with a different email.

---

## 🚀 Running the Project

> Open **2 separate terminal/CMD windows**.

### Terminal 1 — Backend

**Windows:**
```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"
venv\Scripts\activate
set PYTHONPATH=C:\Real-time biscuit quality inspection system with YOLOv8
python backend\app.py
```

**macOS:**
```bash
cd ~/Real-time\ biscuit\ quality\ inspection\ system\ with\ YOLOv8
source venv/bin/activate
export PYTHONPATH=$(pwd)
python backend/app.py
```

Wait for this output before proceeding:
```
════════════════════════════════════════════════════════════
  🍪  BiscuitAI — Real-Time Quality Inspection System
════════════════════════════════════════════════════════════
[DB] Schema initialised
[monaco] Loading models/monaco_best.pt ...
[parle]  Loading models/parle_best.pt  ...
[marie]  Loading models/marie_best.pt  ...
[monaco] ✓ Ready in 3200 ms
[parle]  ✓ Ready in 2900 ms
[marie]  ✓ Ready in 3100 ms
  Server  : http://localhost:5000
════════════════════════════════════════════════════════════
```

> ⚠️ All 3 models must say `✓ Ready` before opening the browser.

### Terminal 2 — Frontend

**Windows:**
```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8\frontend"
npm start
```

**macOS:**
```bash
cd ~/Real-time\ biscuit\ quality\ inspection\ system\ with\ YOLOv8/frontend
npm start
```

Browser opens automatically at **http://localhost:3000**

---

## 🎮 Using the System

```
1. Open http://localhost:3000

2. HOME PAGE
   └── Read about the project → click "Get Started"

3. FEATURES PAGE
   └── Browse all features in card layout

4. LOGIN PAGE
   └── Enter the email you added via add_user.py
   └── Click "Send OTP"
   └── Check your email inbox for the 6-digit code
   └── Enter OTP → you're logged in with a JWT token

5. DETECTION PAGE
   └── Click [Start Camera]        ← webcam/DroidCam activates
   └── Select brand from dropdown  ← Monaco / Parle-G / Marie
   └── Click [Start Batch]         ← batch starts, DB record created
   └── Place 2 biscuits in camera view
   └── Watch live detections appear with:
           Brand name (Monaco / Parle-G / Marie)
           Classification (Good / Broken / Burnt)
           Confidence score (e.g., 94.3%)
   └── Click [Stop Batch]          ← batch finalised in DB
   └── Click [Stop Camera]         ← camera released

6. DASHBOARD PAGE
   └── Per-brand defect vs good percentage charts
   └── Time-based detection trend lines
   └── Hourly production stats
   └── 3-brand comparison charts

7. HISTORY PAGE
   └── Browse all batches with timestamps
   └── Click any batch to see detection log
   └── Click [Export CSV] to download as spreadsheet
```

---

## 🏋️ Dataset Download & Model Training

> Each of the 3 biscuit brands has its own YOLOv8m model trained separately. Combined training caused cross-brand confusion, so models are kept brand-specific.

### Step 1 — Download the Datasets

The dataset zip files are too large for GitHub (50MB+ each). Download all 3 from Google Drive:

> **📥 Google Drive Link:
>       Marie - https://drive.google.com/file/d/1WnDkNyph0YB131u9cx-_UL9BuIKJq6kG/view?usp=sharing
>       Monaco - https://drive.google.com/file/d/1ceLjVMlRiKfc6-_heY06UbRdu_FyXH07/view?usp=sharing
>       Parle - https://drive.google.com/file/d/1d2hGcBAn1bt8Yhq31r26ViVuqG0WkOwH/view?usp=sharing**

The folder contains:
```
Monaco_v10i_yolov8.zip
Parle_v5i_yolov8.zip
Marie_v5i_yolov8.zip
```

After downloading, paste all 3 zip files into:
```
C:\Real-time biscuit quality inspection system with YOLOv8\dataset_zips\
```

Your `dataset_zips\` folder should look like:
```
dataset_zips\
├── Monaco_v10i_yolov8.zip
├── Parle_v5i_yolov8.zip
└── Marie_v5i_yolov8.zip
```

> These are Roboflow exports in YOLOv8 format with bounding boxes and augmentations already applied. Classes in all 3: `['Broken', 'Burnt', 'Good']`

---

### Step 2 — Extract the Datasets Directly to Correct Locations

Run this single command — it creates all required folders and extracts each zip directly into the right location automatically.

**Windows (CMD) — run from project root:**
```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"

python -c "
import zipfile, os

BASE   = r'C:\Real-time biscuit quality inspection system with YOLOv8'
ZIPS   = os.path.join(BASE, 'dataset_zips')

datasets = {
    'Monaco_v10i_yolov8.zip' : os.path.join(BASE, 'training', 'monaco', 'dataset'),
    'Parle_v5i_yolov8.zip'   : os.path.join(BASE, 'training', 'parle',  'dataset'),
    'Marie_v5i_yolov8.zip'   : os.path.join(BASE, 'training', 'marie',  'dataset'),
}

for zip_name, dest in datasets.items():
    zip_path = os.path.join(ZIPS, zip_name)
    if not os.path.exists(zip_path):
        print(f'[SKIP]  {zip_name} not found in dataset_zips\\')
        continue
    os.makedirs(dest, exist_ok=True)
    print(f'[...] Extracting {zip_name} -> {dest}')
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(dest)
    print(f'[ OK] {zip_name} extracted successfully')

print()
print('Done! Verify below:')
for brand in ['monaco', 'parle', 'marie']:
    d = os.path.join(BASE, 'training', brand, 'dataset')
    status = 'OK' if os.path.isdir(os.path.join(d, 'train')) else 'MISSING'
    print(f'  [{status}] training\\{brand}\\dataset\\train\\')
"
```

**macOS (Terminal) — run from project root:**
```bash
cd ~/Real-time\ biscuit\ quality\ inspection\ system\ with\ YOLOv8

python3 -c "
import zipfile, os

BASE   = os.path.expanduser('~/Real-time biscuit quality inspection system with YOLOv8')
ZIPS   = os.path.join(BASE, 'dataset_zips')

datasets = {
    'Monaco_v10i_yolov8.zip' : os.path.join(BASE, 'training', 'monaco', 'dataset'),
    'Parle_v5i_yolov8.zip'   : os.path.join(BASE, 'training', 'parle',  'dataset'),
    'Marie_v5i_yolov8.zip'   : os.path.join(BASE, 'training', 'marie',  'dataset'),
}

for zip_name, dest in datasets.items():
    zip_path = os.path.join(ZIPS, zip_name)
    if not os.path.exists(zip_path):
        print(f'[SKIP]  {zip_name} not found in dataset_zips/')
        continue
    os.makedirs(dest, exist_ok=True)
    print(f'[...] Extracting {zip_name} -> {dest}')
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(dest)
    print(f'[ OK] {zip_name} extracted successfully')

print()
print('Done! Verify below:')
for brand in ['monaco', 'parle', 'marie']:
    d = os.path.join(BASE, 'training', brand, 'dataset')
    status = 'OK' if os.path.isdir(os.path.join(d, 'train')) else 'MISSING'
    print(f'  [{status}] training/{brand}/dataset/train/')
"
```

Expected output after running:
```
[...] Extracting Monaco_v10i_yolov8.zip -> C:\...\training\monaco\dataset
[ OK] Monaco_v10i_yolov8.zip extracted successfully
[...] Extracting Parle_v5i_yolov8.zip  -> C:\...\training\parle\dataset
[ OK] Parle_v5i_yolov8.zip extracted successfully
[...] Extracting Marie_v5i_yolov8.zip  -> C:\...\training\marie\dataset
[ OK] Marie_v5i_yolov8.zip extracted successfully

Done! Verify below:
  [ OK] training\monaco\dataset\train\
  [ OK] training\parle\dataset\train\
  [ OK] training\marie\dataset\train\
```

If any line shows `[SKIP]` — the zip is not in `dataset_zips\`. Check the filename matches exactly.

After extraction each brand folder looks like this:
```
training\marie\
    ├── dataset\                  ← extracted directly here ✓
    │   ├── train\
    │   │   ├── images\
    │   │   └── labels\
    │   ├── valid\
    │   │   ├── images\
    │   │   └── labels\
    │   ├── test\
    │   │   ├── images\
    │   │   └── labels\
    │   ├── data.yaml             ← YOLOv8 dataset config (Roboflow generated)
    │   └── README.roboflow
    ├── runs\                     ← auto-created by YOLOv8 during training
    ├── train_marie.py
    ├── yolo26n.pt
    └── yolov8m.pt
```
Same structure for `training\monaco\` and `training\parle\`.

---

### Step 3 — Train Each Model

Make sure your venv is active and you are in the project root.

**Windows:**
```cmd
cd "C:\Real-time biscuit quality inspection system with YOLOv8"
venv\Scripts\activate
```

**macOS:**
```bash
cd ~/Real-time\ biscuit\ quality\ inspection\ system\ with\ YOLOv8
source venv/bin/activate
```

#### Train Monaco Model
```cmd
python training\monaco\train_monaco.py
```
Training takes approximately **3–5 hours** on CPU, or **30–60 minutes** on GPU.
Watch for output like:
```
Epoch 100/100 ── box_loss: 0.042  cls_loss: 0.018  mAP50: 0.891
Training complete. Best model saved to:
  training\monaco\runs\monaco_YYYYMMDD_HHMMSS\weights\best.pt
```

#### Train Parle-G Model
```cmd
python training\parle\train_parle.py
```

#### Train Marie Model
```cmd
python training\marie\train_marie.py
```

> You can also run all 3 one after another automatically:
> ```cmd
> python scripts\train_all.py
> ```
> This runs Monaco → Parle → Marie sequentially. Leave it running overnight.

---

### Step 4 — Copy best.pt to models\ folder

After each training run, YOLOv8 saves the best weights inside a timestamped folder. You need to copy them to the `models\` folder with the exact filenames the app expects.

**Windows:**
```cmd
REM First, check what your run folder is named:
dir training\monaco\runs\
dir training\parle\runs\
dir training\marie\runs\

REM Then copy (replace the timestamp with your actual folder name):
copy training\monaco\runs\monaco_20250101_120000\weights\best.pt models\monaco_best.pt
copy training\parle\runs\parle_20250101_120000\weights\best.pt   models\parle_best.pt
copy training\marie\runs\marie_20250101_120000\weights\best.pt   models\marie_best.pt
```

**macOS:**
```bash
cp training/monaco/runs/monaco_*/weights/best.pt models/monaco_best.pt
cp training/parle/runs/parle_*/weights/best.pt   models/parle_best.pt
cp training/marie/runs/marie_*/weights/best.pt   models/marie_best.pt
```

After copying, verify:
```cmd
dir models\
```
Expected output:
```
marie_best.pt       XX,XXX,XXX bytes
monaco_best.pt      XX,XXX,XXX bytes
parle_best.pt       XX,XXX,XXX bytes
```

---

### Step 5 — Verify Models Load Correctly

```cmd
python scripts\test_models.py
```

Expected output:
```
[MONACO]
  ✓  File exists  : models/monaco_best.pt (52.3 MB)
  ✓  Loaded       : 3200 ms
  ✓  Inference    : 78 ms
  ✓  Classes      : ['Broken', 'Burnt', 'Good']

[PARLE]
  ✓  File exists  : models/parle_best.pt (52.3 MB)
  ✓  Loaded       : 2900 ms
  ✓  Inference    : 75 ms
  ✓  Classes      : ['Broken', 'Burnt', 'Good']

[MARIE]
  ✓  File exists  : models/marie_best.pt (52.3 MB)
  ✓  Loaded       : 3100 ms
  ✓  Inference    : 80 ms
  ✓  Classes      : ['Broken', 'Burnt', 'Good']

✓  All models verified — ready to run.
```

If any model says `File not found` → go back to Step 4 and verify the copy.

---

### Why YOLOv8m?

| Model | Parameters | mAP@0.5 | CPU Inference | Broken Class Detection |
|-------|-----------|---------|--------------|----------------------|
| YOLOv8n | 3.2M | 37.3% | ~45ms | Poor — misses irregular shapes |
| YOLOv8s | 11.2M | 44.9% | ~80ms | Moderate |
| **YOLOv8m** ✓ | **25.9M** | **50.2%** | **~120ms** | **Best — handles irregular fragments** |

Broken biscuits have no fixed shape or size. YOLOv8m's deeper feature extraction (25.9M parameters vs 3.2M in nano) learns these irregular patterns far better. The extra ~40ms per frame is a worthwhile trade for production accuracy.

---

### Verify Everything Works Before Running

```cmd
REM 1. Test all 3 models load correctly
python scripts\test_models.py

REM 2. Test camera
python scripts\test_camera.py

REM 3. Check MySQL connection
python -c "from backend.utils.db import get_db; conn = get_db(); print('DB OK')"
```

---

## 📊 Detection Logic Summary

```
Frame arrives from camera
       ↓
Run selected brand's YOLOv8m model
       ↓
Filter detections:
  • confidence ≥ 0.25
  • area: 0.2% to 70% of frame
  • aspect ratio ≤ 4.5 (removes thin lines/hands)
       ↓
Non-Maximum Suppression (remove overlapping boxes)
       ↓
Check count == 2 biscuits visible?
  → NO: reset stability buffer, try next frame
  → YES: add to stability buffer
       ↓
3 consecutive frames all agree on same detections?
  → NO: keep buffering
  → YES: CONFIRMED → log to MySQL database
       ↓
Draw bounding boxes on frame
Add label: "Parle-G | Burnt | 94.2%"
Send annotated frame to browser via SocketIO
```


---

## 🤝 Contributing

This is a final year B.Tech project. Contributions, suggestions, and improvements are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---


</div>
