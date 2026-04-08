import { useEffect } from "react";
import { useAuth } from "react-oidc-context";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (auth.isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [auth.isAuthenticated, navigate]);

  const handleLogin = () => {
    auth.signinRedirect();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Org AI Agent</h1>
          <p className="mt-2 text-gray-600">
            Your intelligent assistant for organizational knowledge and workflows.
          </p>
        </div>

        {auth.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            Authentication error: {auth.error.message}
          </div>
        )}

        <button
          onClick={handleLogin}
          disabled={auth.isLoading}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg
                     shadow-sm text-sm font-medium text-white bg-brand-600 hover:bg-brand-700
                     focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Sign in with your organization SSO"
        >
          {auth.isLoading ? "Signing in…" : "Sign in with SSO"}
        </button>
      </div>
    </div>
  );
}
