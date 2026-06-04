// frontend/src/pages/DetectionPage.jsx
// KEY FIX: brand value sent to start_batch matches model key mapping in backend.
// Brand selector disabled during batch so user cannot change brand mid-session.
// Active brand label shown on camera feed.

import React, { useState, useEffect, useRef } from "react";
import { connectSocket } from "../utils/socket";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import {
  Camera, CameraOff, Play, Square,
  Wifi, WifiOff, CheckCircle, AlertTriangle,
  Cookie, Flame, Info
} from "lucide-react";

// Brand config — label shown in UI, value sent to backend
const BRANDS = [
  { label: "Monaco",  value: "Monaco"  },
  { label: "Parle-G", value: "Parle-G" },
  { label: "Marie",   value: "Marie"   },
];

const BRAND_COLORS = {
  "Monaco":  "#f59e0b",
  "Parle-G": "#10b981",
  "Marie":   "#8b5cf6",
};

const QUALITY_COLORS = {
  "Good":    "#10b981",
  "Broken":  "#f97316",
  "Burnt":   "#ef4444",
};

const QUALITY_ICONS = {
  "Good":   CheckCircle,
  "Broken": AlertTriangle,
  "Burnt":  Flame,
};

/* ── Stat card ──────────────────────────────────────────── */
function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "var(--bg-elevated)",
      border: `1px solid var(--border)`,
      borderTop: `3px solid ${color}`,
      borderRadius: "var(--radius-md)",
      padding: "14px 18px",
    }}>
      <div style={{
        fontSize: 28, fontWeight: 700,
        color, fontFamily: "var(--font-head)",
      }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
        {label}
      </div>
    </div>
  );
}

/* ── Single detection result card ───────────────────────── */
function DetectionCard({ det }) {
  const color  = QUALITY_COLORS[det.class] || "#94a3b8";
  const Icon   = QUALITY_ICONS[det.class]  || Cookie;
  const brandC = BRAND_COLORS[det.brand]   || "var(--amber)";
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 12,
      background: "var(--bg-elevated)",
      border: `1px solid ${color}44`,
      borderLeft: `4px solid ${color}`,
      borderRadius: "var(--radius-md)",
      padding: "10px 14px",
      marginBottom: 8,
    }}>
      <Icon size={20} color={color} style={{ flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 14, color }}>
          {det.class}
        </div>
        <div style={{
          fontSize: 12, color: brandC,
          fontWeight: 600, marginTop: 2,
        }}>
          {det.brand}
        </div>
      </div>
      <div style={{
        fontFamily: "var(--font-mono)",
        fontSize: 20, fontWeight: 700, color,
      }}>
        {(det.confidence * 100).toFixed(0)}%
      </div>
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────── */
export default function DetectionPage() {
  const { user }     = useAuth();
  const socketRef    = useRef(null);
  const imgRef       = useRef(null);

  const [connected,   setConnected]   = useState(false);
  const [camActive,   setCamActive]   = useState(false);
  const [batchActive, setBatchActive] = useState(false);
  const [batchId,     setBatchId]     = useState(null);
  const [brand,       setBrand]       = useState("Monaco");   // display name
  const [activeBrand, setActiveBrand] = useState(null);       // brand running in engine
  const [counts,      setCounts]      = useState({ Good: 0, Broken: 0, Burnt: 0, total: 0 });
  const [lastDets,    setLastDets]    = useState([]);
  const [lastInfMs,   setLastInfMs]   = useState(null);
  const [log,         setLog]         = useState([]);

  /* ── Socket setup ─────────────────────────────────────── */
  useEffect(() => {
    const s = connectSocket();
    socketRef.current = s;

    s.on("connect", () => {
      setConnected(true);
      // Re-register socketio on engine via connect event
    });

    s.on("disconnect", () => {
      setConnected(false);
      setCamActive(false);
      setBatchActive(false);
      setActiveBrand(null);
    });

    s.on("status", d => {
      setCamActive(d.camera_active);
      setBatchActive(d.batch_active);
      if (d.active_brand) setActiveBrand(d.active_brand);
    });

    s.on("camera_status", d => {
      setCamActive(d.active);
      if (!d.active) {
        setBatchActive(false);
        setActiveBrand(null);
      }
      if (d.error) toast.error(d.error);
    });

    s.on("batch_status", d => {
      if (d.error) {
        toast.error(d.error);
        return;
      }
      setBatchActive(d.active);
      if (d.batch_id) setBatchId(d.batch_id);
      if (d.brand_key) setActiveBrand(d.brand_key);

      if (!d.active) {
        setActiveBrand(null);
        const c = d.summary?.counts || {};
        toast.success(`Batch #${d.batch_id} done — ${c.total || 0} biscuits`);
        setCounts({ Good: 0, Broken: 0, Burnt: 0, total: 0 });
        setLastDets([]);
      }
    });

    s.on("detection_result", payload => {
      setLastDets(payload.detections);
      setLastInfMs(payload.inference_ms);
      setCounts(prev => {
        const n = { ...prev };
        n.total += payload.detections.length;
        payload.detections.forEach(d => {
          if (d.class in n) n[d.class]++;
        });
        return n;
      });
      setLog(prev => [{
        ts:         new Date().toLocaleTimeString(),
        detections: payload.detections,
        inf_ms:     payload.inference_ms,
      }, ...prev].slice(0, 60));
    });

    // Frame stream — update img src
    s.on("frame", ({ data }) => {
      if (imgRef.current) {
        imgRef.current.src = `data:image/jpeg;base64,${data}`;
      }
    });

    return () => {
      s.off("connect"); s.off("disconnect"); s.off("status");
      s.off("camera_status"); s.off("batch_status");
      s.off("detection_result"); s.off("frame");
    };
  }, []);

  /* ── Controls ─────────────────────────────────────────── */
  const startCamera = () => socketRef.current?.emit("start_camera");
  const stopCamera  = () => socketRef.current?.emit("stop_camera");

  const startBatch  = () => {
    // brand is the display value (e.g. "Parle-G")
    // Backend _brand_to_key() converts it to model key ("parle")
    socketRef.current?.emit("start_batch", {
      user_id: user?.id,
      brand,           // ← send display name, backend maps to model key
    });
  };

  const stopBatch = () => socketRef.current?.emit("stop_batch");

  /* ── Derived ──────────────────────────────────────────── */
  const goodPct   = counts.total ? Math.round(counts.Good   / counts.total * 100) : 0;
  const brokenPct = counts.total ? Math.round(counts.Broken / counts.total * 100) : 0;
  const burntPct  = counts.total ? Math.round(counts.Burnt  / counts.total * 100) : 0;

  const activeBrandDisplay = activeBrand
    ? BRANDS.find(b => b.value.toLowerCase().replace("-", "") === activeBrand.replace("-", ""))?.label
      || activeBrand
    : null;

  const activeBrandColor = activeBrandDisplay
    ? BRAND_COLORS[activeBrandDisplay] || "var(--amber)"
    : "var(--amber)";

  /* ── Render ────────────────────────────────────────────── */
  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
          <h1 style={{ fontFamily: "var(--font-head)", fontSize: 26, fontWeight: 700 }}>
            Live Detection
          </h1>
          <span className={`badge ${connected ? "badge-green" : "badge-red"}`}>
            {connected
              ? <><Wifi size={11} /> Connected</>
              : <><WifiOff size={11} /> Disconnected</>}
          </span>
          {batchActive && activeBrandDisplay && (
            <span className="badge" style={{
              background: `${activeBrandColor}18`,
              color: activeBrandColor,
              border: `1px solid ${activeBrandColor}44`,
            }}>
              ● {activeBrandDisplay} model active
            </span>
          )}
        </div>
        <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
          Select a brand → Start Camera → Start Batch → place 2 biscuits in view.
          Only the selected brand's model will run.
        </p>
      </div>

      {/* Brand info banner */}
      {!batchActive && (
        <div style={{
          background: "rgba(245,158,11,0.08)",
          border: "1px solid rgba(245,158,11,0.2)",
          borderRadius: "var(--radius-md)",
          padding: "10px 16px",
          marginBottom: 20,
          display: "flex", alignItems: "center", gap: 10,
          fontSize: 13, color: "var(--text-secondary)",
        }}>
          <Info size={15} color="var(--amber)" />
          Select a biscuit brand below before starting the batch.
          Only that brand's YOLOv8 model will run — no cross-brand detections.
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 24, alignItems: "start" }}>

        {/* ── LEFT: Camera + Controls ───────────────────── */}
        <div>
          {/* Camera feed */}
          <div style={{
            background: "#000",
            borderRadius: "var(--radius-lg)",
            border: `2px solid ${batchActive ? activeBrandColor : "var(--border)"}`,
            overflow: "hidden",
            aspectRatio: "4/3",
            display: "flex", alignItems: "center", justifyContent: "center",
            position: "relative",
            marginBottom: 16,
            transition: "border-color 0.3s",
          }}>
            {camActive ? (
              <img ref={imgRef} alt="Live detection feed"
                style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
              />
            ) : (
              <div style={{ textAlign: "center", color: "var(--text-muted)" }}>
                <CameraOff size={48} style={{ marginBottom: 12, opacity: 0.4 }} />
                <div style={{ fontSize: 14 }}>Camera is off</div>
                <div style={{ fontSize: 12, marginTop: 4, color: "var(--text-muted)" }}>
                  Click "Start Camera" below
                </div>
              </div>
            )}

            {/* Live overlay badges */}
            {camActive && batchActive && (
              <div style={{
                position: "absolute", top: 10, right: 10,
                display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end",
              }}>
                <span className="badge badge-green" style={{ fontSize: 11 }}>
                  ● BATCH LIVE
                </span>
                {activeBrandDisplay && (
                  <span className="badge" style={{
                    fontSize: 11,
                    background: `${activeBrandColor}22`,
                    color: activeBrandColor,
                    border: `1px solid ${activeBrandColor}55`,
                  }}>
                    {activeBrandDisplay}
                  </span>
                )}
                {lastInfMs !== null && (
                  <span className="badge badge-amber" style={{ fontSize: 10, fontFamily: "var(--font-mono)" }}>
                    {lastInfMs}ms
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Controls row */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>

            {/* Camera button */}
            {!camActive ? (
              <button className="btn btn-primary" onClick={startCamera}
                disabled={!connected}
                style={{ flex: 1, padding: "12px" }}>
                <Camera size={16} /> Start Camera
              </button>
            ) : (
              <button className="btn btn-danger" onClick={stopCamera}
                style={{ flex: 1, padding: "12px" }}>
                <CameraOff size={16} /> Stop Camera
              </button>
            )}

            {/* Brand selector — disabled while batch is running */}
            <div style={{ position: "relative" }}>
              <select
                value={brand}
                onChange={e => setBrand(e.target.value)}
                disabled={batchActive}
                title={batchActive ? "Cannot change brand during active batch" : "Select biscuit brand"}
                style={{
                  background:   "var(--bg-elevated)",
                  border:       batchActive
                    ? `1px solid ${activeBrandColor}55`
                    : "1px solid var(--border-strong)",
                  borderRadius: "var(--radius-md)",
                  color:        batchActive ? activeBrandColor : "var(--text-primary)",
                  fontFamily:   "var(--font-base)",
                  fontWeight:   600,
                  fontSize:     14,
                  padding:      "12px 16px",
                  cursor:       batchActive ? "not-allowed" : "pointer",
                  outline:      "none",
                  minWidth:     140,
                  opacity:      batchActive ? 0.8 : 1,
                }}>
                {BRANDS.map(b => (
                  <option key={b.value} value={b.value}>{b.label}</option>
                ))}
              </select>
              {batchActive && (
                <div style={{
                  position: "absolute", top: -6, right: -6,
                  width: 12, height: 12,
                  background: activeBrandColor,
                  borderRadius: "50%",
                  border: "2px solid var(--bg-base)",
                }} />
              )}
            </div>

            {/* Batch button */}
            {!batchActive ? (
              <button className="btn btn-success" onClick={startBatch}
                disabled={!camActive}
                style={{ flex: 1, padding: "12px" }}>
                <Play size={16} /> Start Batch
              </button>
            ) : (
              <button className="btn btn-danger" onClick={stopBatch}
                style={{ flex: 1, padding: "12px" }}>
                <Square size={16} /> Stop Batch
              </button>
            )}
          </div>

          {/* Stat cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
            <StatCard label="Total"  value={counts.total}  color="#94a3b8" />
            <StatCard label="Good"   value={counts.Good}   color="#10b981" />
            <StatCard label="Broken" value={counts.Broken} color="#f97316" />
            <StatCard label="Burnt"  value={counts.Burnt}  color="#ef4444" />
          </div>

          {/* Quality progress bar */}
          {counts.total > 0 && (
            <div style={{
              marginTop: 14,
              background: "var(--bg-elevated)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              padding: "14px 16px",
            }}>
              <div style={{
                display: "flex", justifyContent: "space-between",
                fontSize: 12, color: "var(--text-secondary)", marginBottom: 8,
              }}>
                <span>Quality breakdown</span>
                <span style={{ fontFamily: "var(--font-mono)" }}>
                  {goodPct}% good · {brokenPct}% broken · {burntPct}% burnt
                </span>
              </div>
              <div style={{
                height: 8, borderRadius: 4,
                background: "var(--bg-base)",
                overflow: "hidden", display: "flex",
              }}>
                <div style={{ width: `${goodPct}%`,   background: "#10b981", transition: "width 0.5s" }} />
                <div style={{ width: `${brokenPct}%`, background: "#f97316", transition: "width 0.5s" }} />
                <div style={{ width: `${burntPct}%`,  background: "#ef4444", transition: "width 0.5s" }} />
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: Detection panel ────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Current detection */}
          <div className="card">
            <div style={{
              fontSize: 11, fontWeight: 700,
              letterSpacing: "1.2px", textTransform: "uppercase",
              color: "var(--amber)", marginBottom: 14,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span>Current Detection</span>
              {lastInfMs && (
                <span style={{
                  fontFamily: "var(--font-mono)", fontSize: 11,
                  color: "var(--text-muted)", fontWeight: 400,
                }}>
                  {lastInfMs}ms
                </span>
              )}
            </div>

            {lastDets.length > 0 ? (
              lastDets.map((d, i) => <DetectionCard key={i} det={d} />)
            ) : (
              <div style={{
                textAlign: "center", color: "var(--text-muted)",
                padding: "28px 0", fontSize: 13,
              }}>
                <Cookie size={36} style={{ marginBottom: 10, opacity: 0.3 }} />
                <div>
                  {batchActive
                    ? `Waiting for ${activeBrandDisplay || brand} biscuits...`
                    : "Start a batch to begin inspection"}
                </div>
                {!batchActive && camActive && (
                  <div style={{ fontSize: 11, marginTop: 6, color: "var(--text-muted)" }}>
                    Selected: <strong style={{ color: BRAND_COLORS[brand] }}>{brand}</strong>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Active batch info */}
          {batchActive && (
            <div style={{
              background: `${activeBrandColor}10`,
              border: `1px solid ${activeBrandColor}33`,
              borderRadius: "var(--radius-md)",
              padding: "12px 16px",
              fontSize: 13,
            }}>
              <div style={{ fontWeight: 600, color: activeBrandColor, marginBottom: 4 }}>
                ● Batch #{batchId} — {activeBrandDisplay}
              </div>
              <div style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                Only <strong style={{ color: activeBrandColor }}>{activeBrandDisplay}</strong> model
                is running. Other brand labels will not appear.
              </div>
            </div>
          )}

          {/* Inspection log */}
          <div className="card" style={{
            maxHeight: 420, overflow: "hidden",
            display: "flex", flexDirection: "column",
          }}>
            <div style={{
              fontSize: 11, fontWeight: 700,
              letterSpacing: "1.2px", textTransform: "uppercase",
              color: "var(--amber)", marginBottom: 12,
              display: "flex", justifyContent: "space-between",
            }}>
              <span>Inspection Log</span>
              <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>
                {log.length} entries
              </span>
            </div>

            <div style={{ overflowY: "auto", flex: 1 }}>
              {log.length === 0 ? (
                <div style={{
                  textAlign: "center", color: "var(--text-muted)",
                  padding: "20px 0", fontSize: 13,
                }}>
                  No entries yet
                </div>
              ) : log.map((entry, i) => (
                <div key={i} style={{
                  borderBottom: "1px solid var(--border)",
                  paddingBottom: 10, marginBottom: 10,
                  fontSize: 13,
                }}>
                  <div style={{
                    display: "flex", justifyContent: "space-between",
                    color: "var(--text-muted)", fontSize: 11, marginBottom: 5,
                  }}>
                    <span>{entry.ts}</span>
                    <span style={{ fontFamily: "var(--font-mono)" }}>{entry.inf_ms}ms</span>
                  </div>
                  {entry.detections.map((d, j) => {
                    const c = QUALITY_COLORS[d.class] || "var(--text-primary)";
                    const bc = BRAND_COLORS[d.brand]  || "var(--text-secondary)";
                    return (
                      <div key={j} style={{
                        display: "flex", justifyContent: "space-between",
                        alignItems: "center", marginBottom: 3,
                      }}>
                        <div>
                          <span style={{ color: bc, fontWeight: 600, fontSize: 12 }}>
                            {d.brand}
                          </span>
                          <span style={{ color: "var(--text-muted)", margin: "0 6px" }}>·</span>
                          <span style={{ color: c, fontWeight: 600 }}>{d.class}</span>
                        </div>
                        <span style={{ fontFamily: "var(--font-mono)", color: c, fontSize: 12 }}>
                          {(d.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}