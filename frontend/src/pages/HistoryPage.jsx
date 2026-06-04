// frontend/src/pages/HistoryPage.jsx
import React, { useState, useEffect, useCallback } from "react";
import {
  ChevronLeft, ChevronRight, Download, Eye, X,
  Calendar, Filter, RefreshCw, Package
} from "lucide-react";
import api from "../utils/api";
import toast from "react-hot-toast";

const BRANDS       = ["All", "Monaco", "Parle-G", "Marie"];
const BRAND_COLORS = { Monaco: "#f59e0b", "Parle-G": "#10b981", Marie: "#8b5cf6" };
const Q_COLORS     = { Good: "#10b981", Broken: "#f97316", Burnt: "#ef4444" };

/* ── tiny helpers ───────────────────────────────────────── */
function fmt(dt) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: true,
  });
}

function duration(start, end) {
  if (!start || !end) return "—";
  const s = Math.round((new Date(end) - new Date(start)) / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

function QBar({ good, broken, burnt, total }) {
  if (!total) return <span style={{ color: "var(--text-muted)", fontSize: 12 }}>—</span>;
  const gp = Math.round((good / total) * 100);
  const bp = Math.round((broken / total) * 100);
  const rp = Math.round((burnt / total) * 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{
        width: 80, height: 6, borderRadius: 3,
        background: "var(--bg-base)", overflow: "hidden", display: "flex",
      }}>
        <div style={{ width: `${gp}%`, background: "#10b981" }} />
        <div style={{ width: `${bp}%`, background: "#f97316" }} />
        <div style={{ width: `${rp}%`, background: "#ef4444" }} />
      </div>
      <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {gp}%
      </span>
    </div>
  );
}

/* ── Batch detail modal ─────────────────────────────────── */
function BatchModal({ batchId, onClose }) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/batches/${batchId}`)
      .then(r => setData(r.data))
      .catch(() => toast.error("Failed to load batch"))
      .finally(() => setLoading(false));
  }, [batchId]);

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)",
      display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "var(--bg-surface)", border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius-xl)", width: "100%", maxWidth: 820,
        maxHeight: "85vh", overflow: "hidden", display: "flex", flexDirection: "column",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "20px 24px", borderBottom: "1px solid var(--border)",
        }}>
          <div>
            <h2 style={{ fontFamily: "var(--font-head)", fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
              Batch #{batchId} — Detail
            </h2>
            {data && (
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                {data.batch.brand} · {data.batch.operator} · {fmt(data.batch.started_at)}
              </div>
            )}
          </div>
          <button onClick={onClose} style={{
            background: "var(--bg-elevated)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)", padding: "6px 10px", cursor: "pointer", color: "var(--text-secondary)",
          }}>
            <X size={16} />
          </button>
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
            <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
          </div>
        ) : data ? (
          <>
            {/* Summary cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, padding: "16px 24px" }}>
              {[
                { label: "Total",   value: data.batch.total_count,   color: "#94a3b8" },
                { label: "Good",    value: data.batch.good_count,    color: "#10b981" },
                { label: "Broken",  value: data.batch.broken_count,  color: "#f97316" },
                { label: "Burnt",   value: data.batch.burnt_count,   color: "#ef4444" },
              ].map(c => (
                <div key={c.label} style={{
                  background: "var(--bg-elevated)", borderRadius: "var(--radius-md)",
                  padding: "12px 16px", borderTop: `3px solid ${c.color}`,
                }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: c.color, fontFamily: "var(--font-head)" }}>
                    {c.value}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{c.label}</div>
                </div>
              ))}
            </div>

            {/* Detections table */}
            <div style={{ overflowY: "auto", flex: 1, padding: "0 24px 24px" }}>
              <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase",
                            color: "var(--amber)", marginBottom: 12 }}>
                Detection Log ({data.detections.length} entries)
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead style={{ position: "sticky", top: 0, background: "var(--bg-surface)" }}>
                  <tr style={{ borderBottom: "1px solid var(--border)" }}>
                    {["#", "Position", "Brand", "Quality", "Confidence", "Inf (ms)", "Time"].map(h => (
                      <th key={h} style={{
                        textAlign: "left", padding: "8px 10px",
                        color: "var(--text-secondary)", fontWeight: 600,
                        fontSize: 11, textTransform: "uppercase", letterSpacing: "0.8px",
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.detections.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                        No detections recorded
                      </td>
                    </tr>
                  ) : data.detections.map((d, i) => (
                    <tr key={d.id}
                      style={{ borderBottom: "1px solid var(--border)", transition: "background 0.15s" }}
                      onMouseEnter={e => e.currentTarget.style.background = "var(--bg-elevated)"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <td style={{ padding: "9px 10px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: 12 }}>
                        {d.id}
                      </td>
                      <td style={{ padding: "9px 10px", color: "var(--text-secondary)" }}>
                        Biscuit {d.biscuit_index}
                      </td>
                      <td style={{ padding: "9px 10px" }}>
                        <span style={{
                          color: BRAND_COLORS[d.brand] || "var(--amber)",
                          fontWeight: 600, fontSize: 12,
                        }}>{d.brand}</span>
                      </td>
                      <td style={{ padding: "9px 10px" }}>
                        <span className="badge" style={{
                          background: `${Q_COLORS[d.quality]}18`,
                          color: Q_COLORS[d.quality] || "var(--text-primary)",
                        }}>
                          {d.quality}
                        </span>
                      </td>
                      <td style={{ padding: "9px 10px", fontFamily: "var(--font-mono)", color: Q_COLORS[d.quality] }}>
                        {parseFloat(d.confidence * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: "9px 10px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: 12 }}>
                        {d.inference_ms ? parseFloat(d.inference_ms).toFixed(1) : "—"}
                      </td>
                      <td style={{ padding: "9px 10px", color: "var(--text-muted)", fontSize: 12 }}>
                        {fmt(d.detected_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Export button */}
            <div style={{ padding: "12px 24px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end" }}>
              <button
                className="btn btn-secondary"
                style={{ gap: 8 }}
                onClick={() => {
                  const token = localStorage.getItem("biscuit_token") || "";
                  const params = new URLSearchParams({ batch_id: batchId, token });
                  window.open(
                    `${process.env.REACT_APP_API_URL}/export/detections?${params.toString()}`,
                    "_blank"
                  );
                }}
              >
                <Download size={14} /> Export Detections CSV
              </button>
            </div>
          </>
        ) : (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
            Failed to load batch data.
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main HistoryPage ───────────────────────────────────── */
export default function HistoryPage() {
  const [batches,     setBatches]     = useState([]);
  const [total,       setTotal]       = useState(0);
  const [page,        setPage]        = useState(1);
  const [pages,       setPages]       = useState(1);
  const [perPage]                     = useState(15);
  const [brandFilter, setBrandFilter] = useState("All");
  const [loading,     setLoading]     = useState(true);
  const [modalId,     setModalId]     = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: perPage });
      if (brandFilter !== "All") params.append("brand", brandFilter);
      const r = await api.get(`/batches/?${params}`);
      setBatches(r.data.batches);
      setTotal(r.data.total);
      setPages(r.data.pages);
    } catch {
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  }, [page, perPage, brandFilter]);

  useEffect(() => { load(); }, [load]);

  // Reset to page 1 when filter changes
  useEffect(() => { setPage(1); }, [brandFilter]);

  const exportBatches = () => {
    const token = localStorage.getItem("biscuit_token") || "";
    const params = new URLSearchParams({ token });
    if (brandFilter !== "All") params.append("brand", brandFilter);
    window.open(
      `${process.env.REACT_APP_API_URL}/export/batches?${params.toString()}`,
      "_blank"
    );
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontFamily: "var(--font-head)", fontSize: 26, fontWeight: 700 }}>
            Inspection History
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 4 }}>
            Complete batch-wise log of all inspection sessions.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button className="btn btn-secondary" onClick={load} style={{ gap: 8 }}>
            <RefreshCw size={14} /> Refresh
          </button>
          <button className="btn btn-secondary" onClick={exportBatches} style={{ gap: 8 }}>
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        display: "flex", gap: 12, alignItems: "center",
        marginBottom: 20, flexWrap: "wrap",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-secondary)", fontSize: 13 }}>
          <Filter size={14} /> Filter by brand:
        </div>
        {BRANDS.map(b => (
          <button key={b} onClick={() => setBrandFilter(b)} style={{
            padding: "6px 14px", borderRadius: "var(--radius-md)", border: "1px solid",
            cursor: "pointer", fontSize: 13, fontWeight: 500, transition: "all 0.15s",
            background: brandFilter === b
              ? (b === "All" ? "rgba(245,158,11,0.15)" : `${BRAND_COLORS[b]}18`)
              : "var(--bg-elevated)",
            color: brandFilter === b
              ? (b === "All" ? "var(--amber)" : BRAND_COLORS[b] || "var(--amber)")
              : "var(--text-secondary)",
            borderColor: brandFilter === b
              ? (b === "All" ? "rgba(245,158,11,0.4)" : `${BRAND_COLORS[b]}55`)
              : "var(--border)",
          }}>
            {b}
          </button>
        ))}
        <span style={{ marginLeft: "auto", fontSize: 13, color: "var(--text-muted)" }}>
          {total} total batches
        </span>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-elevated)" }}>
                {["Batch ID", "Brand", "Operator", "Started At", "Duration", "Total", "Good", "Broken", "Burnt", "Quality", "Actions"].map(h => (
                  <th key={h} style={{
                    textAlign: "left", padding: "12px 16px",
                    color: "var(--text-secondary)", fontWeight: 600,
                    fontSize: 11, textTransform: "uppercase", letterSpacing: "0.8px",
                    whiteSpace: "nowrap",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={11} style={{ padding: 60, textAlign: "center" }}>
                    <div className="spinner" style={{ width: 32, height: 32, borderWidth: 2, margin: "0 auto" }} />
                  </td>
                </tr>
              ) : batches.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ padding: 60, textAlign: "center" }}>
                    <Package size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
                    <div style={{ color: "var(--text-muted)" }}>No batches found</div>
                  </td>
                </tr>
              ) : batches.map(b => (
                <tr key={b.id}
                  style={{ borderBottom: "1px solid var(--border)", transition: "background 0.15s" }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--bg-elevated)"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>

                  <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: 12 }}>
                    #{b.id}
                  </td>

                  <td style={{ padding: "12px 16px" }}>
                    <span className="badge" style={{
                      background: `${BRAND_COLORS[b.brand] || "#f59e0b"}18`,
                      color: BRAND_COLORS[b.brand] || "var(--amber)",
                    }}>
                      {b.brand}
                    </span>
                  </td>

                  <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>
                    {b.operator}
                  </td>

                  <td style={{ padding: "12px 16px", color: "var(--text-muted)", fontSize: 12, whiteSpace: "nowrap" }}>
                    {fmt(b.started_at)}
                  </td>

                  <td style={{ padding: "12px 16px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                    {duration(b.started_at, b.ended_at)}
                  </td>

                  <td style={{ padding: "12px 16px", fontWeight: 700, fontSize: 15 }}>
                    {b.total_count}
                  </td>

                  <td style={{ padding: "12px 16px", color: "#10b981", fontWeight: 600 }}>
                    {b.good_count}
                  </td>

                  <td style={{ padding: "12px 16px", color: "#f97316", fontWeight: 600 }}>
                    {b.broken_count}
                  </td>

                  <td style={{ padding: "12px 16px", color: "#ef4444", fontWeight: 600 }}>
                    {b.burnt_count}
                  </td>

                  <td style={{ padding: "12px 16px", minWidth: 110 }}>
                    <QBar good={b.good_count} broken={b.broken_count}
                          burnt={b.burnt_count}  total={b.total_count} />
                  </td>

                  <td style={{ padding: "12px 16px" }}>
                    <button onClick={() => setModalId(b.id)} style={{
                      display: "flex", alignItems: "center", gap: 6,
                      padding: "6px 12px", borderRadius: "var(--radius-sm)",
                      background: "var(--bg-hover)", border: "1px solid var(--border)",
                      cursor: "pointer", color: "var(--text-secondary)", fontSize: 12,
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.color = "var(--amber)"; e.currentTarget.style.borderColor = "var(--amber)"; }}
                    onMouseLeave={e => { e.currentTarget.style.color = "var(--text-secondary)"; e.currentTarget.style.borderColor = "var(--border)"; }}>
                      <Eye size={13} /> View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "14px 20px", borderTop: "1px solid var(--border)",
          }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Page {page} of {pages}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-secondary"
                style={{ padding: "6px 14px", gap: 6 }}
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}>
                <ChevronLeft size={14} /> Prev
              </button>
              {Array.from({ length: Math.min(pages, 5) }, (_, i) => {
                const p = Math.max(1, Math.min(pages - 4, page - 2)) + i;
                return (
                  <button key={p} onClick={() => setPage(p)} style={{
                    padding: "6px 12px", borderRadius: "var(--radius-sm)",
                    border: "1px solid", cursor: "pointer", fontSize: 13,
                    background: p === page ? "rgba(245,158,11,0.15)" : "var(--bg-elevated)",
                    color: p === page ? "var(--amber)" : "var(--text-secondary)",
                    borderColor: p === page ? "rgba(245,158,11,0.4)" : "var(--border)",
                  }}>
                    {p}
                  </button>
                );
              })}
              <button className="btn btn-secondary"
                style={{ padding: "6px 14px", gap: 6 }}
                disabled={page === pages}
                onClick={() => setPage(p => p + 1)}>
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Batch detail modal */}
      {modalId && <BatchModal batchId={modalId} onClose={() => setModalId(null)} />}
    </div>
  );
}