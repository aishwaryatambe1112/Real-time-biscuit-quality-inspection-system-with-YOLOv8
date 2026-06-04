"""
scripts/test_models.py
----------------------
Verify all 3 trained model files load correctly and can run
a dummy inference before starting the main server.

Usage:
    python scripts/test_models.py
"""
import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

MODELS = {
    "monaco": os.environ.get("MONACO_MODEL_PATH", "models/monaco_best.pt"),
    "parle":  os.environ.get("PARLE_MODEL_PATH",  "models/parle_best.pt"),
    "marie":  os.environ.get("MARIE_MODEL_PATH",  "models/marie_best.pt"),
}

CLASS_NAMES = ["Broken", "Burnt", "Good"]

def test_all():
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERROR] ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    print("\n" + "═" * 52)
    print("  BiscuitAI — Model Verification")
    print("═" * 52)

    all_ok = True
    dummy  = np.zeros((480, 640, 3), dtype=np.uint8)  # blank frame

    for brand, path in MODELS.items():
        print(f"\n  [{brand.upper()}]")
        if not os.path.exists(path):
            print(f"  ✗  File not found: {path}")
            print(f"     → Copy your trained best.pt to this path after training.")
            all_ok = False
            continue

        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  ✓  File exists  : {path} ({size_mb:.1f} MB)")

        try:
            t0    = time.perf_counter()
            model = YOLO(path)
            load_ms = (time.perf_counter() - t0) * 1000
            print(f"  ✓  Loaded       : {load_ms:.0f} ms")

            # Warm-up inference
            t0 = time.perf_counter()
            results = model(dummy, verbose=False)
            inf_ms  = (time.perf_counter() - t0) * 1000
            print(f"  ✓  Inference    : {inf_ms:.1f} ms (warm-up on blank frame)")

            # Check class names
            names = model.names
            print(f"  ✓  Classes      : {list(names.values())}")

            expected = ["Broken", "Burnt", "Good"]
            found    = sorted(names.values())
            if sorted(expected) != sorted(found):
                print(f"  ⚠  WARNING: Expected {expected}, got {found}")

        except Exception as e:
            print(f"  ✗  Load/inference failed: {e}")
            all_ok = False

    print("\n" + "═" * 52)
    if all_ok:
        print("  ✓  All models verified — ready to run.")
    else:
        print("  ✗  Some models failed. Fix the issues above.")
    print("═" * 52 + "\n")

    return all_ok


if __name__ == "__main__":
    ok = test_all()
    sys.exit(0 if ok else 1)
