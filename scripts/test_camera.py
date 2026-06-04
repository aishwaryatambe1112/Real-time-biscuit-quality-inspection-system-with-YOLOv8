"""
scripts/test_camera.py
----------------------
Quick sanity check — opens the webcam and shows a live preview
so you can verify the camera index is correct before starting the system.

Usage:
    python scripts/test_camera.py
    python scripts/test_camera.py --index 1
Press Q to quit.
"""
import sys
import argparse
import cv2


def test_camera(index: int = 0):
    print(f"\n  Testing camera index {index} ...")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print(f"  [ERROR] Cannot open camera {index}.")
        print("  → Check CAMERA_INDEX in .env or try --index 1")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"  [OK] Camera {index} opened — {w}x{h} @ {fps:.0f} fps")
    print(f"  Preview window opened. Press Q to exit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("  [WARNING] Frame read failed")
            break

        cv2.putText(frame, f"Camera {index} — {w}x{h}  |  Press Q to quit",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 180), 2, cv2.LINE_AA)

        cv2.imshow("BiscuitAI — Camera Test", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("  Camera test complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test webcam for BiscuitAI")
    parser.add_argument("--index", type=int, default=0, help="Camera device index (default: 0)")
    args = parser.parse_args()
    test_camera(args.index)
