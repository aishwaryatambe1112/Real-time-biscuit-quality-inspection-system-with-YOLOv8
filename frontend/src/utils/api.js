// frontend/src/utils/api.js
import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:5000/api",
  timeout: 15000,
});

// Attach token if present
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem("biscuit_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// Redirect to login on 401
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem("biscuit_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
