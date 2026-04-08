import { useEffect } from "react";
import { useAuth as useOidcAuth } from "react-oidc-context";

/**
 * Wraps react-oidc-context.
 * Exposes the access token to the axios interceptor via a global slot
 * so we avoid prop-drilling the token through every component.
 */
export function useAuth() {
  const auth = useOidcAuth();

  // Keep the global token slot in sync so api.ts can access it
  useEffect(() => {
    const token = auth.user?.access_token;
    (window as unknown as { __oidc_token?: string }).__oidc_token = token;
  }, [auth.user?.access_token]);

  // Listen for 401 events from axios interceptor and trigger silent renew
  useEffect(() => {
    const handleUnauthorized = async () => {
      try {
        await auth.signinSilent();
      } catch {
        auth.signoutRedirect();
      }
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, [auth]);

  return {
    user: auth.user,
    isAuthenticated: auth.isAuthenticated,
    isLoading: auth.isLoading,
    error: auth.error,
    login: () => auth.signinRedirect(),
    logout: () => auth.signoutRedirect(),
    token: auth.user?.access_token,
  };
}
