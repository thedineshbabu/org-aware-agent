import { ReactNode } from "react";
import { useAuth } from "react-oidc-context";
import { Navigate } from "react-router-dom";

interface Props {
  children: ReactNode;
}

export default function AuthGuard({ children }: Props) {
  const auth = useAuth();

  if (auth.isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-500" />
      </div>
    );
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
