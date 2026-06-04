// frontend/src/pages/LoginPage.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Cookie, Mail, Hash, ArrowLeft, Loader } from "lucide-react";
import toast from "react-hot-toast";
import api from "../utils/api";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate   = useNavigate();
  const [step, setStep]   = useState("email"); // "email" | "otp"
  const [email, setEmail] = useState("");
  const [otp,   setOtp]   = useState("");
  const [busy,  setBusy]  = useState(false);
  const [ttl,   setTtl]   = useState(600);

  const requestOtp = async e => {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    try {
      const r = await api.post("/auth/request-otp", { email: email.trim() });
      toast.success("OTP sent to your email");
      setTtl(r.data.expires_in || 600);
      setStep("otp");
      // Dev helper
      if (r.data.dev_otp) {
        toast(`Dev OTP: ${r.data.dev_otp}`, { icon:"🔑", duration:30000 });
      }
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to send OTP");
    } finally {
      setBusy(false);
    }
  };

  const verifyOtp = async e => {
    e.preventDefault();
    if (!otp.trim()) return;
    setBusy(true);
    try {
      const r = await api.post("/auth/verify-otp", { email, otp: otp.trim() });
      login(r.data.token, r.data.user);
      toast.success(`Welcome, ${r.data.user.name}!`);
      navigate("/detection");
    } catch (err) {
      toast.error(err.response?.data?.error || "Invalid OTP");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{
      minHeight:"100vh",
      background:"radial-gradient(ellipse 80% 60% at 50% 20%,rgba(245,158,11,0.1) 0%,transparent 70%), var(--bg-base)",
      display:"flex",alignItems:"center",justifyContent:"center",
      padding:24,
    }}>
      <div style={{ width:"100%",maxWidth:420 }}>
        {/* Logo */}
        <div style={{ textAlign:"center",marginBottom:40 }}>
          <Link to="/">
            <div style={{ display:"inline-flex",alignItems:"center",gap:12,marginBottom:24 }}>
              <div style={{ width:48,height:48,borderRadius:14,background:"var(--grad-amber)",
                            display:"flex",alignItems:"center",justifyContent:"center",
                            boxShadow:"var(--shadow-amber)" }}>
                <Cookie size={26} color="#000" />
              </div>
              <div style={{ textAlign:"left" }}>
                <div style={{ fontFamily:"var(--font-head)",fontWeight:800,fontSize:22 }}>BiscuitAI</div>
                <div style={{ fontSize:11,color:"var(--text-muted)",letterSpacing:"0.8px",textTransform:"uppercase" }}>
                  Inspection System
                </div>
              </div>
            </div>
          </Link>
          <h1 style={{ fontFamily:"var(--font-head)",fontSize:26,fontWeight:700,marginBottom:8 }}>
            {step==="email" ? "Sign in to your account" : "Enter verification code"}
          </h1>
          <p style={{ color:"var(--text-secondary)",fontSize:14 }}>
            {step==="email"
              ? "We'll send a one-time code to your registered email."
              : `Code sent to ${email}`}
          </p>
        </div>

        {/* Card */}
        <div style={{
          background:"var(--bg-surface)",
          border:"1px solid var(--border-strong)",
          borderRadius:"var(--radius-xl)",
          padding:"32px 32px",
          boxShadow:"var(--shadow-lg)",
        }}>
          {step === "email" ? (
            <form onSubmit={requestOtp} style={{ display:"flex",flexDirection:"column",gap:20 }}>
              <div>
                <label style={{ fontSize:13,fontWeight:500,color:"var(--text-secondary)",
                                display:"block",marginBottom:8 }}>
                  Email address
                </label>
                <div style={{ position:"relative" }}>
                  <Mail size={16} color="var(--text-muted)"
                    style={{ position:"absolute",left:14,top:"50%",transform:"translateY(-50%)" }} />
                  <input
                    className="input"
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={e=>setEmail(e.target.value)}
                    style={{ paddingLeft:42 }}
                    required
                    autoFocus
                  />
                </div>
              </div>
              <button className="btn btn-primary" type="submit" disabled={busy}
                style={{ width:"100%",padding:"13px",fontSize:15 }}>
                {busy ? <><div className="spinner" style={{width:18,height:18}} /> Sending...</>
                      : "Send OTP →"}
              </button>
            </form>
          ) : (
            <form onSubmit={verifyOtp} style={{ display:"flex",flexDirection:"column",gap:20 }}>
              <div>
                <label style={{ fontSize:13,fontWeight:500,color:"var(--text-secondary)",
                                display:"block",marginBottom:8 }}>
                  6-digit OTP code
                </label>
                <div style={{ position:"relative" }}>
                  <Hash size={16} color="var(--text-muted)"
                    style={{ position:"absolute",left:14,top:"50%",transform:"translateY(-50%)" }} />
                  <input
                    className="input"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    placeholder="123456"
                    value={otp}
                    onChange={e=>setOtp(e.target.value.replace(/\D/g,""))}
                    style={{ paddingLeft:42,fontFamily:"var(--font-mono)",fontSize:22,
                             letterSpacing:8,textAlign:"center" }}
                    required
                    autoFocus
                  />
                </div>
                <div style={{ fontSize:12,color:"var(--text-muted)",marginTop:8,textAlign:"right" }}>
                  Expires in {Math.floor(ttl/60)}:{String(ttl%60).padStart(2,"0")}
                </div>
              </div>

              <button className="btn btn-primary" type="submit" disabled={busy || otp.length!==6}
                style={{ width:"100%",padding:"13px",fontSize:15 }}>
                {busy ? <><div className="spinner" style={{width:18,height:18}} /> Verifying...</>
                      : "Verify & Sign In →"}
              </button>

              <button type="button" onClick={()=>{setStep("email");setOtp("");}}
                style={{ background:"none",border:"none",cursor:"pointer",
                         display:"flex",alignItems:"center",gap:6,
                         color:"var(--text-muted)",fontSize:13,justifyContent:"center" }}>
                <ArrowLeft size={14} /> Use different email
              </button>
            </form>
          )}
        </div>

        <div style={{ textAlign:"center",marginTop:28,fontSize:13,color:"var(--text-muted)" }}>
          Need access?{" "}
          <span style={{ color:"var(--amber)" }}>Contact your system administrator.</span>
        </div>
      </div>
    </div>
  );
}
