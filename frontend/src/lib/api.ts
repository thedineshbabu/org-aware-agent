import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 120_000, // LLM calls can take up to 2 minutes
});

// Inject Bearer token from OIDC user store on every request
api.interceptors.request.use((config) => {
  // Token is accessed via the global OIDC context at call time
  const token = (window as unknown as { __oidc_token?: string }).__oidc_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired — trigger silent refresh or redirect to login
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    }
    return Promise.reject(error);
  }
);

export default api;
