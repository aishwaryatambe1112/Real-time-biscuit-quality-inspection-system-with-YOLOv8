"""
scripts/train_all.py
--------------------
Train all 3 biscuit models in sequence.
Assumes dataset ZIPs are in dataset_zips/ folder.

Usage:
    python scripts/train_all.py
    python scripts/train_all.py --brand monaco
"""
import sys
import os
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TRAIN_SCRIPTS = {
    "monaco": "training/monaco/train_monaco.py",
    "parle":  "training/parle/train_parle.py",
    "marie":  "training/marie/train_marie.py",
}


def run_training(brand: str):
    script = TRAIN_SCRIPTS.get(brand)
    if not script or not os.path.exists(script):
        print(f"[ERROR] Training script not found for '{brand}': {script}")
        return False

    print(f"\n{'═'*52}")
    print(f"  Training: {brand.upper()} model")
    print(f"{'═'*52}\n")

    result = subprocess.run(
        [sys.executable, script],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Train BiscuitAI models")
    parser.add_argument(
        "--brand",
        choices=["monaco", "parle", "marie", "all"],
        default="all",
        help="Which brand to train (default: all)",
    )
    args = parser.parse_args()

    brands = list(TRAIN_SCRIPTS.keys()) if args.brand == "all" else [args.brand]

    results = {}
    for brand in brands:
        ok = run_training(brand)
        results[brand] = ok

    print(f"\n{'═'*52}")
    print("  Training Summary")
    print(f"{'═'*52}")
    for brand, ok in results.items():
        status = "✓ SUCCESS" if ok else "✗ FAILED"
        print(f"  {brand:<10} {status}")

    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    print(f"\n  Trained models saved to: {model_dir}")
    for brand in brands:
        pt = os.path.join(model_dir, f"{brand}_best.pt")
        exists = "✓" if os.path.exists(pt) else "✗ MISSING"
        print(f"    {exists}  {pt}")
    print()


if __name__ == "__main__":
    main()
