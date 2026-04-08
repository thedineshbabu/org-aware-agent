import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "react-oidc-context";
import AuthGuard from "./components/AuthGuard";
import Login from "./pages/Login";
import Chat from "./pages/Chat";
import Ingest from "./pages/Ingest";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route
          path="/ingest"
          element={
            <AuthGuard>
              <Ingest />
            </AuthGuard>
          }
        />
        <Route
          path="/*"
          element={
            <AuthGuard>
              <Chat />
            </AuthGuard>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

function AuthCallback() {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (auth.isAuthenticated) {
      navigate("/", { replace: true });
    } else if (auth.error) {
      navigate("/login", { replace: true });
    }
  }, [auth.isAuthenticated, auth.error, navigate]);

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
    </div>
  );
}
