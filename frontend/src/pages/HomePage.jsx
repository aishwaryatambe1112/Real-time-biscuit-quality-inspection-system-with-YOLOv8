// frontend/src/pages/HomePage.jsx
import React from "react";
import { Link } from "react-router-dom";
import { Cookie, ChevronRight, Zap, Shield, BarChart3, Camera } from "lucide-react";

const STATS = [
  { value:"3", label:"Biscuit Brands" },
  { value:"3", label:"Quality Classes" },
  { value:"<50ms", label:"Inference Time" },
  { value:"99%+", label:"Target Accuracy" },
];

const HIGHLIGHTS = [
  { icon: Camera,    title:"Real-Time Detection",  desc:"Live webcam feed processed at up to 20 FPS with multi-model parallel inference." },
  { icon: Zap,       title:"Multi-Model Engine",   desc:"All 3 brand-specific YOLOv8m models run simultaneously on every frame." },
  { icon: Shield,    title:"False-Positive Guard", desc:"Heuristic filters and stability buffering ensure only genuine biscuits get logged." },
  { icon: BarChart3, title:"Rich Analytics",       desc:"Batch-wise history, hourly trends, defect rates, and brand comparisons on the dashboard." },
];

export default function HomePage() {
  return (
    <div style={{ minHeight:"100vh", background:"var(--bg-base)", color:"var(--text-primary)" }}>
      {/* Navbar */}
      <nav style={{
        position:"sticky",top:0,zIndex:50,
        background:"rgba(2,8,23,0.85)",backdropFilter:"blur(12px)",
        borderBottom:"1px solid var(--border)",
        padding:"0 40px", height:64,
        display:"flex", alignItems:"center", justifyContent:"space-between",
      }}>
        <div style={{ display:"flex",alignItems:"center",gap:10 }}>
          <div style={{ width:32,height:32,borderRadius:8,background:"var(--grad-amber)",
                        display:"flex",alignItems:"center",justifyContent:"center" }}>
            <Cookie size={18} color="#000" />
          </div>
          <span style={{ fontFamily:"var(--font-head)",fontWeight:700,fontSize:18 }}>BiscuitAI</span>
        </div>
        <div style={{ display:"flex",gap:8 }}>
          <Link to="/features">
            <button className="btn btn-secondary" style={{ padding:"8px 18px" }}>Features</button>
          </Link>
          <Link to="/login">
            <button className="btn btn-primary" style={{ padding:"8px 18px" }}>
              Sign In <ChevronRight size={14} />
            </button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{
        minHeight:"88vh",
        background:"radial-gradient(ellipse 80% 60% at 50% 0%,rgba(245,158,11,0.12) 0%,transparent 70%), var(--bg-base)",
        display:"flex",alignItems:"center",justifyContent:"center",
        textAlign:"center",padding:"80px 24px",
      }}>
        <div style={{ maxWidth:760 }}>
          <div className="badge badge-amber" style={{ marginBottom:24,fontSize:13,padding:"6px 16px" }}>
            🍪 Industrial AI Quality Control
          </div>

          <h1 style={{
            fontFamily:"var(--font-head)",
            fontSize:"clamp(36px,6vw,72px)",
            fontWeight:800,
            lineHeight:1.1,
            marginBottom:24,
          }}>
            Real-Time Biscuit
            <span className="grad-text" style={{ display:"block" }}>Quality Inspection</span>
          </h1>

          <p style={{ fontSize:18,color:"var(--text-secondary)",lineHeight:1.7,
                      maxWidth:560,margin:"0 auto 40px" }}>
            AI-powered defect detection for Monaco, Parle-G, and Marie biscuits.
            Three specialized YOLOv8m models, one unified inspection dashboard.
          </p>

          <div style={{ display:"flex",gap:12,justifyContent:"center",flexWrap:"wrap" }}>
            <Link to="/login">
              <button className="btn btn-primary" style={{ padding:"14px 32px",fontSize:16 }}>
                Launch System <ChevronRight size={16} />
              </button>
            </Link>
            <Link to="/features">
              <button className="btn btn-secondary" style={{ padding:"14px 32px",fontSize:16 }}>
                Explore Features
              </button>
            </Link>
          </div>

          {/* Stats */}
          <div style={{
            display:"grid",gridTemplateColumns:"repeat(4,1fr)",
            gap:20,marginTop:72,
            background:"var(--bg-surface)",border:"1px solid var(--border)",
            borderRadius:"var(--radius-xl)",padding:"28px 24px",
          }}>
            {STATS.map(s => (
              <div key={s.label}>
                <div style={{ fontFamily:"var(--font-head)",fontSize:32,fontWeight:800,
                              color:"var(--amber)",lineHeight:1 }}>{s.value}</div>
                <div style={{ fontSize:12,color:"var(--text-secondary)",marginTop:6 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Highlights */}
      <section style={{ padding:"80px 40px", maxWidth:1100, margin:"0 auto" }}>
        <div style={{ textAlign:"center",marginBottom:56 }}>
          <div className="section-label">How It Works</div>
          <h2 style={{ fontFamily:"var(--font-head)",fontSize:36,fontWeight:700 }}>
            Built for Production Quality Control
          </h2>
        </div>
        <div style={{ display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:24 }}>
          {HIGHLIGHTS.map(({ icon:Icon, title, desc }) => (
            <div key={title} className="card" style={{
              display:"flex",gap:20,alignItems:"flex-start",
              transition:"border-color 0.2s",
              cursor:"default",
            }}
            onMouseEnter={e=>e.currentTarget.style.borderColor="var(--amber)"}
            onMouseLeave={e=>e.currentTarget.style.borderColor="var(--border)"}>
              <div style={{ width:44,height:44,borderRadius:12,background:"rgba(245,158,11,0.12)",
                            display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0 }}>
                <Icon size={22} color="var(--amber)" />
              </div>
              <div>
                <h3 style={{ fontFamily:"var(--font-head)",fontSize:17,fontWeight:600,marginBottom:8 }}>{title}</h3>
                <p style={{ color:"var(--text-secondary)",fontSize:14,lineHeight:1.6 }}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop:"1px solid var(--border)",padding:"24px 40px",
                       display:"flex",justifyContent:"space-between",alignItems:"center",
                       color:"var(--text-muted)",fontSize:13 }}>
        <span>© 2026 BiscuitAI — Real-Time Quality Inspection System</span>
        <div style={{ display:"flex",gap:16 }}>
          <Link to="/features" style={{ color:"var(--text-muted)" }}>Features</Link>
          <Link to="/login"    style={{ color:"var(--text-muted)" }}>Sign In</Link>
        </div>
      </footer>
    </div>
  );
}
