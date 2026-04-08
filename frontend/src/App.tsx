import { BrowserRouter, Route, Routes } from "react-router-dom";
import AuthGuard from "./components/AuthGuard";
import Login from "./pages/Login";
import Chat from "./pages/Chat";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
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
  // react-oidc-context handles the OIDC callback automatically;
  // this route just exists so the redirect_uri matches.
  return <div className="flex items-center justify-center h-screen">Signing in…</div>;
}
