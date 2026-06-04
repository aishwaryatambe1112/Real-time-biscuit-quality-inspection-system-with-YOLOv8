// frontend/src/components/common/Layout.jsx
import React, { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  Camera, LayoutDashboard, History, LogOut, Menu, X,
  Cookie, ChevronRight
} from "lucide-react";
import toast from "react-hot-toast";

const NAV = [
  { to: "/detection",  icon: Camera,           label: "Detection" },
  { to: "/dashboard",  icon: LayoutDashboard,  label: "Dashboard" },
  { to: "/history",    icon: History,           label: "History" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(true);

  const handleLogout = () => {
    logout();
    toast.success("Logged out");
    navigate("/login");
  };

  return (
    <div style={{ display:"flex", height:"100vh", overflow:"hidden", background:"var(--bg-base)" }}>
      {/* Sidebar */}
      <aside style={{
        width: open ? 240 : 64,
        transition: "width 0.25s ease",
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        zIndex: 10,
      }}>
        {/* Logo */}
        <div style={{ padding:"20px 16px", display:"flex", alignItems:"center", gap:12,
                      borderBottom:"1px solid var(--border)", minHeight:72 }}>
          <div style={{ width:36,height:36,borderRadius:10,background:"var(--grad-amber)",
                        display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0 }}>
            <Cookie size={20} color="#000" />
          </div>
          {open && (
            <div>
              <div style={{ fontFamily:"var(--font-head)",fontWeight:700,fontSize:15,color:"var(--text-primary)" }}>
                BiscuitAI
              </div>
              <div style={{ fontSize:10,color:"var(--text-muted)",letterSpacing:"0.8px",textTransform:"uppercase" }}>
                Quality System
              </div>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:"16px 8px", display:"flex", flexDirection:"column", gap:4 }}>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} style={{ textDecoration:"none" }}>
              {({ isActive }) => (
                <div style={{
                  display:"flex", alignItems:"center", gap:12,
                  padding:"10px 12px", borderRadius:"var(--radius-md)",
                  background: isActive ? "rgba(245,158,11,0.12)" : "transparent",
                  color: isActive ? "var(--amber)" : "var(--text-secondary)",
                  fontWeight: isActive ? 600 : 400,
                  fontSize:14,
                  transition:"all 0.15s",
                  cursor:"pointer",
                  whiteSpace:"nowrap",
                  overflow:"hidden",
                  borderLeft: isActive ? "3px solid var(--amber)" : "3px solid transparent",
                }}>
                  <Icon size={18} style={{ flexShrink:0 }} />
                  {open && <span>{label}</span>}
                </div>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User + logout */}
        <div style={{ padding:"12px 8px", borderTop:"1px solid var(--border)" }}>
          {open && (
            <div style={{ padding:"8px 12px", marginBottom:8 }}>
              <div style={{ fontSize:13,fontWeight:600,color:"var(--text-primary)",
                            overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap" }}>
                {user?.name}
              </div>
              <div style={{ fontSize:11,color:"var(--text-muted)" }}>{user?.role}</div>
            </div>
          )}
          <button onClick={handleLogout} style={{
            width:"100%",display:"flex",alignItems:"center",gap:12,
            padding:"10px 12px",borderRadius:"var(--radius-md)",
            background:"transparent",border:"none",cursor:"pointer",
            color:"var(--text-secondary)",fontSize:14,transition:"all 0.15s",
          }}
          onMouseEnter={e=>e.currentTarget.style.color="#f87171"}
          onMouseLeave={e=>e.currentTarget.style.color="var(--text-secondary)"}>
            <LogOut size={18} style={{ flexShrink:0 }} />
            {open && <span>Logout</span>}
          </button>
        </div>

        {/* Toggle */}
        <button onClick={()=>setOpen(o=>!o)} style={{
          position:"absolute", bottom:80, left: open ? 228 : 52,
          width:24,height:24,borderRadius:"50%",
          background:"var(--bg-elevated)",border:"1px solid var(--border-strong)",
          cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",
          transition:"left 0.25s ease",zIndex:20,
        }}>
          {open ? <X size={12} color="var(--text-secondary)" />
                : <ChevronRight size={12} color="var(--text-secondary)" />}
        </button>
      </aside>

      {/* Main */}
      <main style={{ flex:1, overflow:"auto", padding:"28px 32px" }}>
        <Outlet />
      </main>
    </div>
  );
}
