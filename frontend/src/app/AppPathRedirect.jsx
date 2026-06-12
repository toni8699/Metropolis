import { Navigate, useParams } from "react-router-dom";

/** Legacy paths (/book/1) → /app/book/1 */
export function AppPathRedirect({ prefix }) {
  const params = useParams();
  const suffix = Object.values(params).join("/");
  const target = suffix ? `${prefix}/${suffix}` : prefix;
  return <Navigate to={target} replace />;
}
