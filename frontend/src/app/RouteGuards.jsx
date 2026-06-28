import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export function RequireAuth() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/app" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

export function RequireHost() {
  const { isAuthenticated, isAdmin, hasListings } = useAuth();
  const location = useLocation();
  if (isAdmin) {
    return <Navigate to="/admin" replace />;
  }
  if (!isAuthenticated || !hasListings) {
    return <Navigate to="/app" replace state={{ deniedFrom: location.pathname }} />;
  }
  return <Outlet />;
}

export function RequireRole({ roles }) {
  const { role, isAdmin } = useAuth();
  const location = useLocation();
  const wanted = roles || [];
  const allowed = (wanted.includes("admin") && isAdmin) || wanted.includes(role);
  if (!allowed) {
    return <Navigate to="/app" replace state={{ deniedFrom: location.pathname }} />;
  }
  return <Outlet />;
}
