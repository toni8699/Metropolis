export default function BodyCard({ children, className = "" }) {
  return <div className={`neo-card ${className}`}>{children}</div>;
}
