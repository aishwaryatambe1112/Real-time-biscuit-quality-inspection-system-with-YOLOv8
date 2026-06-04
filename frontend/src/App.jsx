// frontend/src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/common/Layout";
import HomePage     from "./pages/HomePage";
import FeaturesPage from "./pages/FeaturesPage";
import LoginPage    from "./pages/LoginPage";
import DetectionPage from "./pages/DetectionPage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage   from "./pages/HistoryPage";
import "./styles/global.css";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",
                 height:"100vh",background:"var(--bg-base)"}}>
      <div className="spinner" style={{width:40,height:40,borderWidth:3}} />
    </div>
  );
  return user ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <Navigate to="/detection" replace /> : children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              border: "1px solid var(--border-strong)",
              fontFamily: "var(--font-base)",
            },
            success: { iconTheme: { primary: "#10b981", secondary: "#000" } },
            error:   { iconTheme: { primary: "#ef4444", secondary: "#000" } },
          }}
        />
        <Routes>
          {/* Public */}
          <Route path="/" element={<HomePage />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/login" element={
            <PublicRoute><LoginPage /></PublicRoute>
          } />
          {/* Protected — inside layout shell */}
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/detection"  element={<DetectionPage />} />
            <Route path="/dashboard"  element={<DashboardPage />} />
            <Route path="/history"    element={<HistoryPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}