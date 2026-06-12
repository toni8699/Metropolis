import { Navigate } from "react-router-dom";
import HostDashboard from "@/features/host/components/HostDashboard";
import { useAuth } from "@/context/AuthContext";

export default function OwnerDashboardPage() {
  const { isAdmin } = useAuth();
  if (isAdmin) {
    return <Navigate to="/admin" replace />;
  }
  return <HostDashboard mode="owner" />;
}
