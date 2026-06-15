import { Navigate } from "react-router-dom";
import HostDashboard from "@/features/host/components/HostDashboard";
import { useAuth } from "@/context/AuthContext";

export default function HostDashboardPage({ mode = "owner" }) {
  const { isAdmin } = useAuth();
  if (mode === "owner" && isAdmin) {
    return <Navigate to="/admin" replace />;
  }
  return <HostDashboard mode={mode} />;
}
