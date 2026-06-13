export default function VroomLogo({ className = "" }) {
  return (
    <img
      src="/vroom-logo.svg"
      alt="VROOM Logo"
      className={`h-12 w-auto drop-shadow-md transition-transform hover:scale-110 ${className}`}
    />
  );
}
