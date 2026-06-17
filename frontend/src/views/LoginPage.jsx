import { Navigate, Link, useNavigate, useSearchParams } from "react-router-dom";
import AuthModal from "@/shared/components/AuthModal";
import VroomLogo from "@/layout/VroomLogo";
import { useAuth } from "@/context/AuthContext";
import { safeRedirectPath } from "@/shared/lib/redirectPath";

export default function LoginPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectTo = safeRedirectPath(searchParams.get("redirect_to"));

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSuccess = () => {
    navigate(redirectTo, { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-vroom-bg px-4 py-10">
      <Link to="/app" className="mb-8">
        <VroomLogo />
      </Link>
      <AuthModal
        isOpen
        mode="login"
        onClose={() => navigate("/app", { replace: true })}
        onSuccess={handleSuccess}
      />
    </div>
  );
}
