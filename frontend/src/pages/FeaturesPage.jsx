// frontend/src/pages/FeaturesPage.jsx
import React from "react";
import { Link } from "react-router-dom";
import {
  Camera, Zap, BarChart3, Shield, Database, Download,
  Cookie, BrainCircuit, Layers, Clock, AlertTriangle, CheckCircle,
  ChevronLeft
} from "lucide-react";

const FEATURES = [
  {
    icon: BrainCircuit, color:"#f59e0b",
    title:"Multi-Model Parallel Inference",
    desc:"Three specialized YOLOv8m models — one per brand — run simultaneously on every camera frame using Python threading. Detections are merged, overlapping boxes resolved by highest confidence.",
    points:["Monaco model — oval cream biscuit specialist","Parle-G model — square glucose biscuit specialist","Marie model — round tea biscuit specialist","All three run in parallel, results merged per frame"],
  },
  {
    icon: Shield, color:"#10b981",
    title:"False-Positive Prevention",
    desc:"Strict heuristic filters prevent hands, faces, or background objects from being logged as biscuits. Stability buffering requires consistent detections across multiple consecutive frames.",
    points:["Aspect-ratio filter: rejects elongated shapes (hands, arms)","Area filter: rejects objects too small or too large","Confidence threshold: 55% minimum per detection","Stability buffer: 3 consecutive matching frames required"],
  },
  {
    icon: Layers, color:"#8b5cf6",
    title:"Batch-Based Workflow",
    desc:"Inspection is organized in batches — Start Camera → Start Batch → inspect biscuits → Stop Batch → Stop Camera. Each batch is independently tracked with full statistics.",
    points:["Operator-controlled batch lifecycle","Per-batch Good / Broken / Burnt counts","Batch stored with timestamp, brand, and operator","Complete audit trail in MySQL database"],
  },
  {
    icon: BarChart3, color:"#3b82f6",
    title:"Rich Analytics Dashboard",
    desc:"Comprehensive charts and KPIs built with Recharts. Analyze quality trends over time, compare brands, and identify defect patterns at a glance.",
    points:["Hourly trend line charts per brand","Defect vs Good donut charts per brand","3-brand side-by-side comparison bar chart","Today's live count summary cards"],
  },
  {
    icon: Clock, color:"#f97316",
    title:"Real-Time Detection Feed",
    desc:"Live annotated camera feed streamed to browser via WebSocket. Each detection overlay shows: Brand | Quality | Confidence %. Inference time displayed in corner.",
    points:["Annotated MJPEG over SocketIO (~20 FPS)","Color-coded boxes: Green=Good, Orange=Broken, Red=Burnt","Brand + Class + Confidence on each bounding box","Inference latency shown on frame"],
  },
  {
    icon: Database, color:"#06b6d4",
    title:"MySQL Persistence",
    desc:"Every confirmed detection is stored in a relational MySQL database. Hourly aggregation table enables fast dashboard queries without scanning millions of rows.",
    points:["Users, OTP tokens, batches, detections tables","Stored procedure for hourly stats upsert","Full foreign-key integrity with ON DELETE CASCADE","Optimized indexes for time-range dashboard queries"],
  },
  {
    icon: Download, color:"#84cc16",
    title:"CSV Export",
    desc:"Export full batch history or detection logs to CSV in one click. Filter by brand or batch before exporting for targeted analysis.",
    points:["Export all batches to batches_export.csv","Export all detections to detections_export.csv","Filter by brand or specific batch","Compatible with Excel, Google Sheets, Power BI"],
  },
  {
    icon: Camera, color:"#ec4899",
    title:"OTP-Based Secure Login",
    desc:"No passwords stored. Authentication uses time-limited one-time codes sent via SendGrid email. JWT tokens authorize all subsequent API calls.",
    points:["6-digit OTP via SendGrid transactional email","OTP expires in 10 minutes, single-use","SHA-256 hashed in database — plaintext never stored","JWT (24h expiry) for session management"],
  },
];

export default function FeaturesPage() {
  return (
    <div style={{ minHeight:"100vh",background:"var(--bg-base)",color:"var(--text-primary)" }}>
      {/* Nav */}
      <nav style={{
        position:"sticky",top:0,zIndex:50,
        background:"rgba(2,8,23,0.85)",backdropFilter:"blur(12px)",
        borderBottom:"1px solid var(--border)",
        padding:"0 40px",height:64,
        display:"flex",alignItems:"center",gap:16,
      }}>
        <Link to="/" style={{ display:"flex",alignItems:"center",gap:6,color:"var(--text-secondary)",fontSize:14 }}>
          <ChevronLeft size={16} /> Back
        </Link>
        <div style={{ width:1,height:20,background:"var(--border)" }} />
        <div style={{ display:"flex",alignItems:"center",gap:10 }}>
          <div style={{ width:28,height:28,borderRadius:7,background:"var(--grad-amber)",
                        display:"flex",alignItems:"center",justifyContent:"center" }}>
            <Cookie size={15} color="#000" />
          </div>
          <span style={{ fontFamily:"var(--font-head)",fontWeight:700 }}>BiscuitAI — Features</span>
        </div>
        <div style={{ marginLeft:"auto" }}>
          <Link to="/login">
            <button className="btn btn-primary" style={{ padding:"8px 18px" }}>Sign In</button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{
        padding:"72px 40px 56px",textAlign:"center",
        background:"radial-gradient(ellipse 70% 50% at 50% 0%,rgba(245,158,11,0.1) 0%,transparent 70%)",
      }}>
        <div className="section-label">Platform Capabilities</div>
        <h1 style={{ fontFamily:"var(--font-head)",fontSize:"clamp(28px,5vw,52px)",
                     fontWeight:800,marginBottom:20 }}>
          Everything You Need for
          <span className="grad-text"> Quality Control</span>
        </h1>
        <p style={{ color:"var(--text-secondary)",fontSize:17,maxWidth:560,margin:"0 auto",lineHeight:1.7 }}>
          From AI inference to database persistence to export — the full
          production-grade inspection pipeline, explained.
        </p>
      </section>

      {/* Feature cards */}
      <section style={{ padding:"0 40px 80px",maxWidth:1200,margin:"0 auto" }}>
        <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(520px,1fr))",gap:24 }}>
          {FEATURES.map(({ icon:Icon, color, title, desc, points }) => (
            <div key={title} className="card" style={{
              transition:"border-color 0.2s,transform 0.2s,box-shadow 0.2s",
              cursor:"default",
            }}
            onMouseEnter={e=>{
              e.currentTarget.style.borderColor=color;
              e.currentTarget.style.transform="translateY(-2px)";
              e.currentTarget.style.boxShadow=`0 8px 32px ${color}22`;
            }}
            onMouseLeave={e=>{
              e.currentTarget.style.borderColor="var(--border)";
              e.currentTarget.style.transform="none";
              e.currentTarget.style.boxShadow="none";
            }}>
              <div style={{ display:"flex",alignItems:"flex-start",gap:16,marginBottom:16 }}>
                <div style={{ width:48,height:48,borderRadius:12,flexShrink:0,
                              background:`${color}18`,display:"flex",alignItems:"center",justifyContent:"center" }}>
                  <Icon size={24} color={color} />
                </div>
                <h3 style={{ fontFamily:"var(--font-head)",fontSize:18,fontWeight:700,lineHeight:1.3,
                             paddingTop:4 }}>{title}</h3>
              </div>
              <p style={{ color:"var(--text-secondary)",fontSize:14,lineHeight:1.7,marginBottom:16 }}>{desc}</p>
              <ul style={{ listStyle:"none",display:"flex",flexDirection:"column",gap:8 }}>
                {points.map(p => (
                  <li key={p} style={{ display:"flex",alignItems:"flex-start",gap:8,
                                       fontSize:13,color:"var(--text-secondary)" }}>
                    <CheckCircle size={14} color={color} style={{ flexShrink:0,marginTop:2 }} />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{
        margin:"0 40px 80px",borderRadius:"var(--radius-xl)",
        background:"linear-gradient(135deg,rgba(245,158,11,0.15) 0%,rgba(139,92,246,0.1) 100%)",
        border:"1px solid rgba(245,158,11,0.3)",
        padding:"56px 48px",textAlign:"center",
      }}>
        <h2 style={{ fontFamily:"var(--font-head)",fontSize:32,fontWeight:800,marginBottom:16 }}>
          Ready to Inspect?
        </h2>
        <p style={{ color:"var(--text-secondary)",marginBottom:32,fontSize:16 }}>
          Sign in and start your first inspection batch in under a minute.
        </p>
        <Link to="/login">
          <button className="btn btn-primary" style={{ padding:"14px 40px",fontSize:16 }}>
            Get Started →
          </button>
        </Link>
      </section>
    </div>
  );
}
