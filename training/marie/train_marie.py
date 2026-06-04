"""
=============================================================
Train Marie Biscuit Detector — YOLOv8m
=============================================================
Usage:
    python training/marie/train_marie.py
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import yaml

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] ultralytics not found. Run: pip install ultralytics")
    sys.exit(1)

PROJECT_ROOT  = Path(__file__).resolve().parents[2]
DATASET_ZIP   = PROJECT_ROOT / "dataset_zips" / "Marie.v5i.yolov8.zip"
DATASET_DIR   = PROJECT_ROOT / "training" / "marie" / "dataset"
RUNS_DIR      = PROJECT_ROOT / "training" / "marie" / "runs"
MODELS_DIR    = PROJECT_ROOT / "models"
DATA_YAML     = DATASET_DIR / "data.yaml"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def prepare_dataset():
    if DATASET_DIR.exists():
        print("[INFO] Dataset already extracted.")
    else:
        print(f"[INFO] Extracting {DATASET_ZIP} ...")
        if not DATASET_ZIP.exists():
            print(f"[ERROR] ZIP not found at {DATASET_ZIP}")
            print("  Place the Roboflow zip at:", DATASET_ZIP)
            sys.exit(1)
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(DATASET_ZIP, 'r') as z:
            z.extractall(DATASET_DIR)
        print("[INFO] Extraction complete.")

    with open(DATA_YAML, 'r') as f:
        cfg = yaml.safe_load(f)

    cfg['train'] = str(DATASET_DIR / "train" / "images")
    cfg['val']   = str(DATASET_DIR / "valid" / "images")
    cfg['test']  = str(DATASET_DIR / "test"  / "images")

    with open(DATA_YAML, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False)

    print("[INFO] data.yaml paths updated.")
    return cfg


def train():
    cfg = prepare_dataset()
    print(f"\n[INFO] Classes: {cfg['names']}")
    print("[INFO] Starting Marie YOLOv8m training ...\n")

    model = YOLO("yolov8m.pt")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name  = f"marie_{timestamp}"

    results = model.train(
        data       = str(DATA_YAML),
        epochs     = 80,
        imgsz      = 512,
        batch      = 16,
        workers    = 8,
        device     = "0" if _gpu() else "cpu",
        project    = str(RUNS_DIR),
        name       = run_name,
        exist_ok   = False,
        pretrained = True,
        optimizer  = "AdamW",
        lr0        = 0.001,
        lrf        = 0.01,
        momentum   = 0.937,
        weight_decay = 0.0005,
        warmup_epochs = 3,
        warmup_momentum = 0.8,
        box        = 7.5,
        cls        = 0.5,
        dfl        = 1.5,
        hsv_h      = 0.015,
        hsv_s      = 0.7,
        hsv_v      = 0.4,
        degrees    = 5.0,
        translate  = 0.1,
        scale      = 0.5,
        flipud     = 0.1,
        fliplr     = 0.5,
        mosaic     = 0.8,
        mixup      = 0.1,
        copy_paste = 0.1,
        verbose    = True,
        save       = True,
        save_period= 10,
        plots      = True,
        amp        = True,
    )

    best_src = RUNS_DIR / run_name / "weights" / "best.pt"
    best_dst = MODELS_DIR / "marie_best.pt"
    if best_src.exists():
        shutil.copy(best_src, best_dst)
        print(f"\n[SUCCESS] Best model saved → {best_dst}")
    else:
        print("[WARNING] best.pt not found in run folder.")

    print("\n--- Training Complete ---")
    print(f"  Run folder : {RUNS_DIR / run_name}")
    print(f"  Model      : {best_dst}")
    return results


def _gpu():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


if __name__ == "__main__":
    train()