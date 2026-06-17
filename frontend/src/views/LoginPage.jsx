import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import AuthModal from "@/shared/components/AuthModal";
import Layout from "@/layout/Layout";
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
    <Layout onSearch={() => {}} onHome={() => navigate("/")}>
      <AuthModal
        isOpen
        mode="login"
        onClose={() => navigate("/app", { replace: true })}
        onSuccess={handleSuccess}
      />
    </Layout>
  );
}
