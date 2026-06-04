"""
=============================================================
Real-Time Biscuit Quality Inspection — Multi-Model Engine
=============================================================
Architecture:
  • ALL 3 YOLOv8m models loaded at startup (Monaco/Parle/Marie)
  • Every frame runs through ALL 3 models simultaneously
    via Python threading (one thread per model)
  • Detections merged; overlapping boxes keep highest confidence
  • Each detection carries its own brand label
  • Stability buffer (STABILITY_FRAMES) before DB log
  • Heuristic filters reject hands/faces (aspect ratio, area)
  • Expects EXPECTED_COUNT=10 biscuits — logs only on clean pair
=============================================================
"""

import cv2, os, time, threading, queue, logging, base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, List
import numpy as np

logger = logging.getLogger("detection_engine")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics not installed")

CLASS_NAMES        = ["Broken", "Burnt", "Good"]
BISCUIT_BRANDS     = {"monaco": "Monaco", "parle": "Parle-G", "marie": "Marie"}
CONF_THRESHOLD     = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.55))
IOU_THRESHOLD      = float(os.environ.get("IOU_THRESHOLD", 0.45))
MERGE_IOU          = 0.40
STABILITY_FRAMES   = 3
EXPECTED_COUNT     = 10
MAX_ASPECT_RATIO   = 3.5
MIN_BBOX_AREA_FRAC = 0.005
MAX_BBOX_AREA_FRAC = 0.60
FRAME_SKIP         = int(os.environ.get("FRAME_SKIP", 1))
COLOR_MAP = {"Good":(57,255,20), "Broken":(0,165,255), "Burnt":(0,0,220)}


def _iou(a, b):
    ix1=max(a[0],b[0]); iy1=max(a[1],b[1])
    ix2=min(a[2],b[2]); iy2=min(a[3],b[3])
    iw=max(0,ix2-ix1); ih=max(0,iy2-iy1); inter=iw*ih
    if inter==0: return 0.0
    return inter/((a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter+1e-6)


def _merge_detections(dets: List[dict]) -> List[dict]:
    kept=[]; used=[False]*len(dets)
    sd = sorted(enumerate(dets), key=lambda x: -x[1]["confidence"])
    for idx,det in sd:
        if used[idx]: continue
        kept.append(det)
        for jdx,other in sd:
            if jdx==idx or used[jdx]: continue
            if _iou(det["bbox"],other["bbox"])>MERGE_IOU: used[jdx]=True
        used[idx]=True
    return kept


class DetectionEngine:
    def __init__(self, model_paths: Dict[str,str], camera_index: int=0):
        self.model_paths  = {k:Path(v) for k,v in model_paths.items()}
        self.camera_index = camera_index
        self._models: Dict[str,"YOLO"] = {}
        self._models_lock  = threading.Lock()
        self._cap          = None
        self._cam_running  = threading.Event()
        self._cam_thread   = None
        self._frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self._latest_jpeg  = None
        self._jpeg_lock    = threading.Lock()
        self._batch_active = False
        self._batch_start  = None
        self._log_callback: Optional[Callable] = None
        self._stability_buffer: List[List[dict]] = []
        self._batch_counts = {"Good":0,"Broken":0,"Burnt":0,"total":0}
        self._batch_lock   = threading.Lock()
        self._infer_thread = None
        self._infer_running= threading.Event()
        self._preload_all_models()
        logger.info("DetectionEngine ready — all models loaded")

    # ── Model loading ──────────────────────────────────────
    def _preload_all_models(self):
        for brand in self.model_paths:
            self._load_model(brand)

    def _load_model(self, brand: str) -> bool:
        brand = brand.lower()
        with self._models_lock:
            if brand in self._models: return True
            path = self.model_paths.get(brand)
            if not path or not path.exists():
                logger.error(f"Model missing for '{brand}': {path}"); return False
            if not YOLO_AVAILABLE: return False
            logger.info(f"Loading [{brand}]: {path}")
            m = YOLO(str(path))
            m.overrides.update({"conf":CONF_THRESHOLD,"iou":IOU_THRESHOLD,"max_det":6,"verbose":False})
            self._models[brand] = m
            logger.info(f"  ✓ {brand} loaded")
            return True

    @property
    def loaded_brands(self): return list(self._models.keys())

    # ── Camera ─────────────────────────────────────────────
    def start_camera(self) -> bool:
        if self._cam_running.is_set(): return True
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened(): cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened(): logger.error(f"Cannot open camera {self.camera_index}"); return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        cap.set(cv2.CAP_PROP_FPS,30);           cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
        self._cap = cap; self._cam_running.set()
        self._cam_thread = threading.Thread(target=self._camera_loop, daemon=True, name="CamCapture")
        self._cam_thread.start(); logger.info("Camera started"); return True

    def stop_camera(self):
        self._cam_running.clear()
        if self._cam_thread and self._cam_thread.is_alive(): self._cam_thread.join(timeout=3)
        if self._cap: self._cap.release(); self._cap=None
        while not self._frame_queue.empty():
            try: self._frame_queue.get_nowait()
            except queue.Empty: break
        logger.info("Camera stopped")

    def _camera_loop(self):
        skip=0
        while self._cam_running.is_set():
            ret,frame = self._cap.read()
            if not ret: time.sleep(0.05); continue
            skip+=1
            if skip%FRAME_SKIP!=0: continue
            if self._frame_queue.full():
                try: self._frame_queue.get_nowait()
                except queue.Empty: pass
            try: self._frame_queue.put_nowait(frame)
            except queue.Full: pass

    # ── Batch ──────────────────────────────────────────────
    def start_batch(self, log_callback: Callable):
        if not self._models: raise RuntimeError("No models loaded")
        self._log_callback=log_callback; self._batch_active=True
        self._batch_start=datetime.utcnow(); self._stability_buffer.clear()
        self._batch_counts={"Good":0,"Broken":0,"Burnt":0,"total":0}
        self._infer_running.set()
        self._infer_thread=threading.Thread(target=self._inference_loop,daemon=True,name="Inference")
        self._infer_thread.start(); logger.info("Batch started")

    def stop_batch(self) -> dict:
        self._infer_running.clear(); self._batch_active=False
        if self._infer_thread and self._infer_thread.is_alive(): self._infer_thread.join(timeout=5)
        with self._batch_lock:
            summary={"start_time":self._batch_start.isoformat() if self._batch_start else None,
                     "end_time":datetime.utcnow().isoformat(),"counts":dict(self._batch_counts)}
        logger.info(f"Batch stopped — {summary}"); return summary

    # ── Multi-model inference loop ─────────────────────────
    def _inference_loop(self):
        while self._infer_running.is_set():
            try: frame=self._frame_queue.get(timeout=0.5)
            except queue.Empty: continue

            h,w=frame.shape[:2]; frame_area=h*w
            t0=time.perf_counter()

            # Run ALL models in parallel threads
            results_map: Dict[str,object] = {}
            def _run(brand, model, frm):
                results_map[brand] = model(frm, verbose=False)[0]

            with self._models_lock: snap=dict(self._models)
            threads=[threading.Thread(target=_run,args=(b,m,frame),daemon=True) for b,m in snap.items()]
            for t in threads: t.start()
            for t in threads: t.join(timeout=2.0)

            inf_ms=(time.perf_counter()-t0)*1000

            # Collect + filter detections from all models
            all_dets=[]
            for brand,result in results_map.items():
                if result.boxes is None: continue
                boxes  = result.boxes.xyxy.cpu().numpy()
                confs  = result.boxes.conf.cpu().numpy()
                labels = result.boxes.cls.cpu().numpy().astype(int)
                for box,conf,lbl in zip(boxes,confs,labels):
                    x1,y1,x2,y2=box; bw=x2-x1; bh=y2-y1; area=bw*bh
                    if conf<CONF_THRESHOLD: continue
                    af=area/frame_area
                    if af<MIN_BBOX_AREA_FRAC or af>MAX_BBOX_AREA_FRAC: continue
                    if max(bw,bh)/(min(bw,bh)+1e-6)>MAX_ASPECT_RATIO: continue
                    cname=CLASS_NAMES[lbl] if lbl<len(CLASS_NAMES) else "Unknown"
                    all_dets.append({"brand":BISCUIT_BRANDS.get(brand,brand),
                                     "brand_key":brand,"class":cname,
                                     "confidence":float(conf),
                                     "bbox":[float(x1),float(y1),float(x2),float(y2)]})

            merged=_merge_detections(all_dets)
            annotated=self._draw(frame.copy(), merged, inf_ms)
            self._push_jpeg(annotated)

            if len(merged)==EXPECTED_COUNT:
                self._stability_buffer.append(merged)
            else:
                self._stability_buffer.clear(); continue

            self._stability_buffer=self._stability_buffer[-STABILITY_FRAMES:]
            if len(self._stability_buffer)==STABILITY_FRAMES and self._stable():
                confirmed=self._stability_buffer[-1]
                self._stability_buffer.clear()
                self._emit(confirmed, inf_ms)

    def _stable(self) -> bool:
        def sig(dets): return tuple(sorted((d["brand"],d["class"]) for d in dets))
        ref=sig(self._stability_buffer[0])
        return all(sig(f)==ref for f in self._stability_buffer[1:])

    def _emit(self, detections: List[dict], inf_ms: float):
        with self._batch_lock:
            self._batch_counts["total"]+=len(detections)
            for d in detections:
                if d["class"] in self._batch_counts: self._batch_counts[d["class"]]+=1
        if self._log_callback:
            try: self._log_callback({"detections":detections,
                                      "timestamp":datetime.utcnow().isoformat(),
                                      "inference_ms":round(inf_ms,1)})
            except Exception as e: logger.error(f"Callback error: {e}")

    # ── Drawing ────────────────────────────────────────────
    def _draw(self, frame, dets, inf_ms):
        for det in dets:
            x1,y1,x2,y2=[int(v) for v in det["bbox"]]
            color=COLOR_MAP.get(det["class"],(200,200,200))
            cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
            label=f"{det['brand']} | {det['class']} | {det['confidence']:.0%}"
            (tw,th),_=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.55,1)
            cv2.rectangle(frame,(x1,y1-th-10),(x1+tw+6,y1),color,-1)
            cv2.putText(frame,label,(x1+3,y1-5),cv2.FONT_HERSHEY_SIMPLEX,0.55,(255,255,255),1,cv2.LINE_AA)
        sc=(57,255,20) if len(dets)==EXPECTED_COUNT else (0,0,220)
        cv2.putText(frame,f"Inf: {inf_ms:.1f}ms",(8,22),cv2.FONT_HERSHEY_SIMPLEX,0.55,(255,255,0),1,cv2.LINE_AA)
        cv2.putText(frame,f"Det: {len(dets)}/{EXPECTED_COUNT}",(8,44),cv2.FONT_HERSHEY_SIMPLEX,0.55,sc,1,cv2.LINE_AA)
        return frame

    # ── Output ─────────────────────────────────────────────
    def _push_jpeg(self, frame):
        _,buf=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,75])
        with self._jpeg_lock: self._latest_jpeg=buf.tobytes()

    def get_frame_jpeg(self) -> Optional[bytes]:
        with self._jpeg_lock: return self._latest_jpeg

    def get_frame_b64(self) -> Optional[str]:
        j=self.get_frame_jpeg(); return base64.b64encode(j).decode() if j else None

    @property
    def is_camera_active(self): return self._cam_running.is_set()
    @property
    def is_batch_active(self): return self._batch_active
    @property
    def batch_counts(self):
        with self._batch_lock: return dict(self._batch_counts)

        