// frontend/src/pages/DashboardPage.jsx
import React, { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadialBarChart, RadialBar,
} from "recharts";
import { TrendingUp, Cookie, AlertTriangle, CheckCircle, RefreshCw } from "lucide-react";
import api from "../utils/api";
import toast from "react-hot-toast";

const BRAND_COLORS = { Monaco:"#f59e0b", "Parle-G":"#10b981", Marie:"#8b5cf6" };
const Q_COLORS = { Good:"#10b981", Broken:"#f97316", Burnt:"#ef4444" };
const DONUT_COLORS = ["#10b981","#f97316","#ef4444"];

function KpiCard({ label, value, sub, color, icon: Icon }) {
  return (
    <div className="card" style={{ borderTop:`3px solid ${color}` }}>
      <div style={{ display:"flex",justifyContent:"space-between",alignItems:"flex-start" }}>
        <div>
          <div style={{ fontSize:12,color:"var(--text-secondary)",marginBottom:8 }}>{label}</div>
          <div style={{ fontFamily:"var(--font-head)",fontSize:32,fontWeight:800,color }}>
            {value ?? "—"}
          </div>
          {sub && <div style={{ fontSize:12,color:"var(--text-muted)",marginTop:4 }}>{sub}</div>}
        </div>
        <div style={{ width:44,height:44,borderRadius:12,background:`${color}18`,
                      display:"flex",alignItems:"center",justifyContent:"center" }}>
          <Icon size={22} color={color} />
        </div>
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:"var(--bg-elevated)",border:"1px solid var(--border-strong)",
                  borderRadius:"var(--radius-md)",padding:"10px 14px",fontSize:13 }}>
      <div style={{ marginBottom:6,color:"var(--text-secondary)" }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color:p.color,fontWeight:500 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

export default function DashboardPage() {
  const [summary,    setSummary]    = useState(null);
  const [trend,      setTrend]      = useState([]);
  const [defectRate, setDefectRate] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [recent,     setRecent]     = useState([]);
  const [trendHours, setTrendHours] = useState(24);
  const [loading,    setLoading]    = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [s, t, d, c, r] = await Promise.all([
        api.get("/dashboard/summary"),
        api.get(`/dashboard/trend?hours=${trendHours}`),
        api.get("/dashboard/defect-rate"),
        api.get("/dashboard/comparison"),
        api.get("/dashboard/recent-batches?limit=8"),
      ]);
      setSummary(s.data);
      setTrend(t.data);
      setDefectRate(d.data);
      setComparison(c.data);
      setRecent(r.data);
    } catch { toast.error("Failed to load dashboard"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [trendHours]);

  const overall = summary?.overall;

  // Format trend data for recharts
  const trendFormatted = trend.reduce((acc, row) => {
    const hour = new Date(row.hour_bucket).toLocaleString("en-IN",{hour:"2-digit",minute:"2-digit",hour12:true});
    const existing = acc.find(r=>r.hour===hour);
    if (existing) {
      existing[row.brand + "_good"]    = (existing[row.brand+"_good"]||0)   + row.good_count;
      existing[row.brand + "_broken"]  = (existing[row.brand+"_broken"]||0) + row.broken_count;
      existing[row.brand + "_burnt"]   = (existing[row.brand+"_burnt"]||0)  + row.burnt_count;
    } else {
      const entry = { hour };
      entry[row.brand+"_good"]   = row.good_count;
      entry[row.brand+"_broken"] = row.broken_count;
      entry[row.brand+"_burnt"]  = row.burnt_count;
      acc.push(entry);
    }
    return acc;
  }, []);

  if (loading) return (
    <div style={{ display:"flex",alignItems:"center",justifyContent:"center",height:400 }}>
      <div className="spinner" style={{ width:40,height:40,borderWidth:3 }} />
    </div>
  );

  return (
    <div>
      {/* Header */}
      <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:28 }}>
        <div>
          <h1 style={{ fontFamily:"var(--font-head)",fontSize:26,fontWeight:700 }}>Dashboard</h1>
          <p style={{ color:"var(--text-secondary)",fontSize:14 }}>
            Quality analytics across all inspection batches
          </p>
        </div>
        <button className="btn btn-secondary" onClick={load} style={{ gap:8 }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* KPI row */}
      <div style={{ display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:16,marginBottom:24 }}>
        <KpiCard label="Total Inspected" value={overall?.total ?? 0}
          color="#f59e0b" icon={Cookie} sub={`${summary?.batch_count||0} batches`} />
        <KpiCard label="Good Biscuits"   value={overall?.good ?? 0}
          color="#10b981" icon={CheckCircle}
          sub={overall?.total ? `${Math.round(overall.good/overall.total*100)}%` : ""} />
        <KpiCard label="Broken"          value={overall?.broken ?? 0}
          color="#f97316" icon={AlertTriangle}
          sub={overall?.total ? `${Math.round(overall.broken/overall.total*100)}%` : ""} />
        <KpiCard label="Burnt"           value={overall?.burnt ?? 0}
          color="#ef4444" icon={TrendingUp}
          sub={overall?.total ? `${Math.round(overall.burnt/overall.total*100)}%` : ""} />
      </div>

      {/* Row 1: Trend + Defect rate */}
      <div style={{ display:"grid",gridTemplateColumns:"2fr 1fr",gap:20,marginBottom:20 }}>
        {/* Trend line */}
        <div className="card">
          <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20 }}>
            <div>
              <div className="section-label">Production Trend</div>
              <div style={{ fontFamily:"var(--font-head)",fontWeight:600 }}>Good biscuits over time</div>
            </div>
            <select value={trendHours} onChange={e=>setTrendHours(Number(e.target.value))}
              style={{ background:"var(--bg-elevated)",border:"1px solid var(--border-strong)",
                       borderRadius:"var(--radius-sm)",color:"var(--text-primary)",
                       fontSize:13,padding:"6px 12px",cursor:"pointer",outline:"none" }}>
              <option value={6}>Last 6h</option>
              <option value={24}>Last 24h</option>
              <option value={72}>Last 3 days</option>
              <option value={168}>Last week</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendFormatted}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="hour" tick={{fontSize:11,fill:"var(--text-muted)"}} />
              <YAxis tick={{fontSize:11,fill:"var(--text-muted)"}} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{fontSize:12}} />
              {["Monaco","Parle-G","Marie"].map(b=>(
                <Line key={b} type="monotone" dataKey={`${b}_good`} name={`${b} Good`}
                  stroke={BRAND_COLORS[b]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Defect donut per brand */}
        <div className="card">
          <div className="section-label">Defect Rate by Brand</div>
          <div style={{ fontFamily:"var(--font-head)",fontWeight:600,marginBottom:16 }}>
            Good vs Defective
          </div>
          <div style={{ display:"flex",flexDirection:"column",gap:16 }}>
            {defectRate.map(r => (
              <div key={r.brand}>
                <div style={{ display:"flex",justifyContent:"space-between",fontSize:13,marginBottom:4 }}>
                  <span style={{ fontWeight:600,color:BRAND_COLORS[r.brand]||"var(--amber)" }}>{r.brand}</span>
                  <span style={{ color:"var(--text-muted)" }}>
                    {r.good_pct}% good · {r.defect_pct}% defect
                  </span>
                </div>
                <div style={{ height:8,borderRadius:4,background:"var(--bg-base)",overflow:"hidden",display:"flex" }}>
                  <div style={{ width:`${r.good_pct}%`,background:"#10b981",transition:"width 0.5s" }} />
                  <div style={{ width:`${r.broken_pct}%`,background:"#f97316",transition:"width 0.5s" }} />
                  <div style={{ width:`${r.burnt_pct}%`,background:"#ef4444",transition:"width 0.5s" }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Comparison bar + Summary pie */}
      <div style={{ display:"grid",gridTemplateColumns:"3fr 2fr",gap:20,marginBottom:20 }}>
        {/* Brand comparison */}
        <div className="card">
          <div className="section-label">Brand Comparison</div>
          <div style={{ fontFamily:"var(--font-head)",fontWeight:600,marginBottom:20 }}>
            All brands — Good / Broken / Burnt
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={comparison}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="brand" tick={{fontSize:12,fill:"var(--text-secondary)"}} />
              <YAxis tick={{fontSize:11,fill:"var(--text-muted)"}} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{fontSize:12}} />
              <Bar dataKey="good"    name="Good"    fill="#10b981" radius={[4,4,0,0]} />
              <Bar dataKey="broken"  name="Broken"  fill="#f97316" radius={[4,4,0,0]} />
              <Bar dataKey="burnt"   name="Burnt"   fill="#ef4444" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Overall pie — FIXED */}
        <div className="card" style={{ display:"flex", flexDirection:"column" }}>
          <div className="section-label">Overall Quality Split</div>
          <div style={{ fontFamily:"var(--font-head)", fontWeight:600, marginBottom:8 }}>
            All brands combined
          </div>

          {/* Show pie only when there is actual data */}
          {(() => {
            const goodVal   = Number(overall?.good)   || 0;
            const brokenVal = Number(overall?.broken) || 0;
            const burntVal  = Number(overall?.burnt)  || 0;
            const totalVal  = goodVal + brokenVal + burntVal;

            const pieData = [
              { name: "Good",   value: goodVal,   color: "#10b981" },
              { name: "Broken", value: brokenVal, color: "#f97316" },
              { name: "Burnt",  value: burntVal,  color: "#ef4444" },
            ].filter(d => d.value > 0);   // remove zero-value slices so chart renders

            if (totalVal === 0 || pieData.length === 0) {
              return (
                <div style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "32px 0",
                  color: "var(--text-muted)",
                  fontSize: 13,
                  gap: 8,
                }}>
                  <div style={{ fontSize: 32, opacity: 0.3 }}>◔</div>
                  <div>No data yet</div>
                  <div style={{ fontSize: 11 }}>Run a batch to see quality split</div>
                </div>
              );
            }

            return (
              <>
                {/* Big stat numbers */}
                <div style={{ display:"flex", gap:12, marginBottom:12, flexWrap:"wrap" }}>
                  {[
                    { label:"Good",   val:goodVal,   color:"#10b981" },
                    { label:"Broken", val:brokenVal, color:"#f97316" },
                    { label:"Burnt",  val:burntVal,  color:"#ef4444" },
                  ].map(s => (
                    <div key={s.label} style={{
                      flex:1, minWidth:60,
                      background:`${s.color}12`,
                      border:`1px solid ${s.color}33`,
                      borderRadius:"var(--radius-md)",
                      padding:"8px 10px",
                      textAlign:"center",
                    }}>
                      <div style={{ fontSize:20, fontWeight:700, color:s.color, fontFamily:"var(--font-head)" }}>
                        {s.val}
                      </div>
                      <div style={{ fontSize:10, color:"var(--text-muted)", marginTop:2 }}>{s.label}</div>
                      <div style={{ fontSize:11, color:s.color, fontWeight:600 }}>
                        {Math.round(s.val / totalVal * 100)}%
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pie chart */}
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart margin={{ top:0, right:0, bottom:0, left:0 }}>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="45%"
                      innerRadius={55}
                      outerRadius={85}
                      paddingAngle={pieData.length > 1 ? 3 : 0}
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) =>
                        percent > 0.05 ? `${Math.round(percent * 100)}%` : ""
                      }
                      labelLine={false}
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={`cell-${i}`} fill={entry.color} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value, name) => [
                        `${value} (${Math.round(value / totalVal * 100)}%)`,
                        name,
                      ]}
                      contentStyle={{
                        background: "var(--bg-elevated)",
                        border: "1px solid var(--border-strong)",
                        borderRadius: "var(--radius-md)",
                        fontSize: 13,
                      }}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={10}
                      wrapperStyle={{ fontSize:12, paddingTop:8 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </>
            );
          })()}
        </div>
      </div>

      {/* Recent batches table */}
      <div className="card">
        <div className="section-label">Recent Batches</div>
        <div style={{ fontFamily:"var(--font-head)",fontWeight:600,marginBottom:16 }}>
          Last 8 inspection batches
        </div>
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%",borderCollapse:"collapse",fontSize:13 }}>
            <thead>
              <tr style={{ borderBottom:"1px solid var(--border)" }}>
                {["ID","Brand","Operator","Started","Total","Good","Broken","Burnt"].map(h=>(
                  <th key={h} style={{ textAlign:"left",padding:"8px 12px",
                                       color:"var(--text-secondary)",fontWeight:600,
                                       fontSize:11,textTransform:"uppercase",letterSpacing:"0.8px" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recent.map(b=>(
                <tr key={b.id} style={{ borderBottom:"1px solid var(--border)" }}
                  onMouseEnter={e=>e.currentTarget.style.background="var(--bg-elevated)"}
                  onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                  <td style={{ padding:"10px 12px",fontFamily:"var(--font-mono)",color:"var(--text-muted)" }}>
                    #{b.id}
                  </td>
                  <td style={{ padding:"10px 12px" }}>
                    <span className="badge" style={{
                      background:`${BRAND_COLORS[b.brand]}18`,
                      color: BRAND_COLORS[b.brand]||"var(--amber)",
                    }}>
                      {b.brand}
                    </span>
                  </td>
                  <td style={{ padding:"10px 12px",color:"var(--text-secondary)" }}>{b.operator}</td>
                  <td style={{ padding:"10px 12px",color:"var(--text-muted)",fontFamily:"var(--font-mono)",fontSize:12 }}>
                    {b.started_at ? new Date(b.started_at).toLocaleString("en-IN") : "—"}
                  </td>
                  <td style={{ padding:"10px 12px",fontWeight:600 }}>{b.total_count}</td>
                  <td style={{ padding:"10px 12px",color:"#10b981",fontWeight:600 }}>{b.good_count}</td>
                  <td style={{ padding:"10px 12px",color:"#f97316",fontWeight:600 }}>{b.broken_count}</td>
                  <td style={{ padding:"10px 12px",color:"#ef4444",fontWeight:600 }}>{b.burnt_count}</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr><td colSpan={8} style={{ padding:"24px",textAlign:"center",color:"var(--text-muted)" }}>
                  No batches yet
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}